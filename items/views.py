from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import F, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView

from items.forms import ItemForm, ItemImageFormSet
from items.models import Item, ItemLike, Report
from notifications.services import notify

REPORT_SUSPENSION_THRESHOLD = 5
REPORT_SUSPENSION_DAYS = 5
REPORT_HIDE_THRESHOLD = 3


class ItemListView(ListView):
    model = Item
    template_name = 'items/item_list.html'
    context_object_name = 'items'
    paginate_by = 20

    def get_queryset(self):
        queryset = (
            Item.objects.filter(is_hidden=False)
            .select_related('seller', 'region')
            .order_by('-created_at')
        )
        query = self.request.GET.get('q', '').strip()
        if query:
            queryset = queryset.filter(description__icontains=query)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '').strip()
        return context


class ItemDetailView(DetailView):
    model = Item
    template_name = 'items/item_detail.html'
    context_object_name = 'item'

    def get_queryset(self):
        base = Item.objects.select_related('seller', 'region').prefetch_related('images')
        user = self.request.user
        if user.is_authenticated and user.is_staff:
            return base
        if user.is_authenticated:
            return base.filter(Q(is_hidden=False) | Q(seller_id=user.id))
        return base.filter(is_hidden=False)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['is_liked'] = (
            user.is_authenticated and self.object.likes.filter(user=user).exists()
        )
        context['status_choices'] = Item.Status.choices
        return context


class ToggleLikeView(LoginRequiredMixin, View):
    def post(self, request, pk):
        item = get_object_or_404(Item, pk=pk)
        like, created = ItemLike.objects.get_or_create(item=item, user=request.user)
        if created:
            Item.objects.filter(pk=item.pk).update(like_count=F('like_count') + 1)
        else:
            like.delete()
            Item.objects.filter(pk=item.pk).update(like_count=F('like_count') - 1)
        item.refresh_from_db(fields=['like_count'])
        return JsonResponse({'liked': created, 'like_count': item.like_count})


class ReportItemView(LoginRequiredMixin, View):
    def get(self, request, pk):
        item = get_object_or_404(Item.objects.select_related('seller'), pk=pk)
        if item.seller_id == request.user.id:
            return redirect('items:detail', pk=item.pk)
        if Report.objects.filter(item=item, reporter=request.user).exists():
            messages.warning(request, '이미 신고처리된 게시물입니다.')
            return redirect('items:detail', pk=item.pk)
        return render(request, 'items/report_form.html', {
            'item': item,
            'reasons': Report.Reason.choices,
        })

    def post(self, request, pk):
        item = get_object_or_404(Item.objects.select_related('seller'), pk=pk)
        if item.seller_id == request.user.id:
            return redirect('items:detail', pk=item.pk)

        reason = request.POST.get('reason')
        valid_reasons = {value for value, _ in Report.Reason.choices}
        if reason not in valid_reasons:
            return render(request, 'items/report_form.html', {
                'item': item,
                'reasons': Report.Reason.choices,
                'error': '신고 사유를 선택해주세요.',
            })

        _, created = Report.objects.get_or_create(
            item=item, reporter=request.user, defaults={'reason': reason}
        )
        if not created:
            messages.warning(request, '이미 신고처리된 게시물입니다.')
        if created:
            notify(item.seller, 'report', '내 게시물이 신고되었습니다.', f'/{item.id}/')

            item_report_count = Report.objects.filter(item=item).count()
            if item_report_count >= REPORT_HIDE_THRESHOLD and not item.is_hidden:
                item.is_hidden = True
                item.save(update_fields=['is_hidden'])

            seller_report_count = Report.objects.filter(item__seller=item.seller).count()
            if seller_report_count >= REPORT_SUSPENSION_THRESHOLD:
                item.seller.suspended_until = timezone.now() + timedelta(
                    days=REPORT_SUSPENSION_DAYS
                )
                item.seller.save(update_fields=['suspended_until'])

        return redirect('items:detail', pk=item.pk)


class ItemWithImagesMixin:
    """Shared logic for handling the ItemImageFormSet alongside ItemForm."""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['image_formset'] = ItemImageFormSet(
                self.request.POST, self.request.FILES, instance=self.object
            )
        else:
            context['image_formset'] = ItemImageFormSet(instance=self.object)
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        image_formset = context['image_formset']
        form.instance.seller = self.request.user
        response = super().form_valid(form)
        if image_formset.is_valid():
            image_formset.instance = self.object
            image_formset.save()
        return response


class ItemCreateView(LoginRequiredMixin, ItemWithImagesMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = 'items/item_form.html'
    success_url = reverse_lazy('items:list')


class ItemOwnerRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.get_object().seller_id == self.request.user.id


class ItemStatusUpdateView(LoginRequiredMixin, ItemOwnerRequiredMixin, View):
    def get_object(self):
        return get_object_or_404(Item, pk=self.kwargs['pk'])

    def post(self, request, pk):
        item = self.get_object()
        status = request.POST.get('status')
        valid_statuses = {value for value, _ in Item.Status.choices}
        if status not in valid_statuses:
            messages.error(request, '올바르지 않은 거래 상태입니다.')
        else:
            item.status = status
            item.save(update_fields=['status'])
        return redirect('items:detail', pk=item.pk)


class ItemUpdateView(LoginRequiredMixin, ItemOwnerRequiredMixin, UpdateView):
    model = Item
    form_class = ItemForm
    template_name = 'items/item_form.html'

    def get_success_url(self):
        return reverse_lazy('items:detail', kwargs={'pk': self.object.pk})


class ItemDeleteView(LoginRequiredMixin, ItemOwnerRequiredMixin, DeleteView):
    model = Item
    template_name = 'items/item_confirm_delete.html'
    success_url = reverse_lazy('items:list')
