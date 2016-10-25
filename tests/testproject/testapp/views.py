from django.views.generic.edit import CreateView
from django.core.urlresolvers import reverse_lazy

from . import models


class BasicModelCreateVeiw(CreateView):
    """Create ``BasicModel``"""
    model = models.BasicModel
    fields = ('some_num', 'some_txt', 'some_date')
    template_name = 'form.html'
    success_url = reverse_lazy('new')
