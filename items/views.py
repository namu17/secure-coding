from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView

from items.forms import ItemForm, ItemImageFormSet
from items.models import Item


class ItemListView(ListView):
    model = Item
    template_name = 'items/item_list.html'
    context_object_name = 'items'
    paginate_by = 20
    queryset = Item.objects.select_related('seller', 'region').order_by('-created_at')


class ItemDetailView(DetailView):
    model = Item
    template_name = 'items/item_detail.html'
    context_object_name = 'item'
    queryset = Item.objects.select_related('seller', 'region').prefetch_related('images')


class ItemCreateView(LoginRequiredMixin, CreateView):
    model = Item
    form_class = ItemForm
    template_name = 'items/item_form.html'
    success_url = reverse_lazy('items:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.method == 'POST':
            context['image_formset'] = ItemImageFormSet(self.request.POST, self.request.FILES)
        else:
            context['image_formset'] = ItemImageFormSet()
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
