from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.views.generic.base import TemplateView, RedirectView
from django.views.generic.detail import DetailView
from expenses.models import *
from django.core.urlresolvers import reverse_lazy
from expenses.forms import *
from auth.views import LoginRequiredViewMixin
from django.shortcuts import redirect
from django.http import Http404, HttpResponseRedirect
from django.contrib import messages
from django.utils.translation import ugettext_lazy as _
from extra_views import SearchableListMixin

class Home(TemplateView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            return redirect('group_list')
        return super(Home, self).dispatch(request, *args, **kwargs)


class GroupList(LoginRequiredViewMixin, ListView):
    model = Group

    def get_queryset(self):
        return self.request.user.expense_groups.all()


class GroupCreate(LoginRequiredViewMixin, CreateView):
    model = Group
    form_class = GroupForm

    def form_valid(self, form):
        self.object = form.save()
        self.object.users.add(self.request.user)
        return super(GroupCreate, self).form_valid(form) 


class GroupUpdate(LoginRequiredViewMixin, UpdateView):
    model = Group
    form_class = GroupForm


class GroupDelete(LoginRequiredViewMixin, DeleteView):
    model = Group
    success_url = reverse_lazy('group_list')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        success_url = self.get_success_url()
        print(self.object.users.count())
        if self.object.users.count()>1:
            self.object.users.remove(request.user)
        else:
            self.object.delete()
        return HttpResponseRedirect(success_url)


class InviteCreate(LoginRequiredViewMixin, DetailView):
    template_name = "expenses/invite_create.html"
    model = Group

    def get_queryset(self):
        return self.request.user.expense_groups.all()


class InviteDetail(LoginRequiredViewMixin, DetailView):
    template_name = "expenses/invite_detail.html"
    model = Group

    def get_object(self,queryset=None):
        group = super(InviteDetail, self).get_object()
        if self.kwargs['hash'] == group.invite_code:
            return group
        else:
            raise Http404


class InviteAccept(LoginRequiredViewMixin, RedirectView):
    template_name = "expenses/invite_accept.html"
    http_method_names = ['post',]

    def post(self, request, *args, **kwargs):
        group = Group.objects.get(pk=self.kwargs['pk'])
        if self.kwargs['hash'] == group.invite_code:
            group.users.add(request.user)
            messages.add_message(request, messages.SUCCESS, _('Invite accepted! You may now share expenses with the group.'))
            return redirect(group.get_absolute_url())
        else:
            raise Http404


class ExpenseViewMixin(object):
    model = Expense

    def get_queryset(self):
        try:
            return self.request.user.expense_groups.get(pk=self.kwargs['group']).expense_set.all()
        except Group.DoesNotExist:
            raise Http404

    def get_form_kwargs(self, **kwargs):
        kwargs = super(ExpenseViewMixin, self).get_form_kwargs(**kwargs)
        kwargs['users'] = self.request.user.expense_groups.get(pk=self.kwargs['group']).users.all()
        return kwargs

    def get_success_url(self):
        return reverse_lazy('expense_list',kwargs={'group':self.kwargs['group']})


class ExpenseList(SearchableListMixin, ExpenseViewMixin, LoginRequiredViewMixin, ListView):
    paginate_by = 20
    search_fields = ['title', 'description']
    def get_context_data(self, **kwargs):
        group = self.request.user.expense_groups.get(pk=self.kwargs['group'])
        context = super(ExpenseList, self).get_context_data(**kwargs)
        context['group'] = group
        context['users'] = group.users_with_totals(self.request.user)
        return context


class ExpenseCreate(ExpenseViewMixin, LoginRequiredViewMixin, CreateView):
    form_class = ExpenseForm

    def get_initial(self):
        initial = super(ExpenseCreate, self).get_initial()
        initial = initial.copy()
        initial['user'] = self.request.user
        return initial

    def form_valid(self, form):
        try:
            form.instance.group = self.request.user.expense_groups.get(pk=self.kwargs['group'])
        except Group.DoesNotExist:
            raise Http404

        return super(ExpenseCreate, self).form_valid(form)

    def get_success_url(self):
        if self.request.POST.get('add_another', None):
            return reverse('expense_create', kwargs={'group': self.kwargs['group']})
        return super(ExpenseCreate, self).get_success_url()


class ExpenseUpdate(ExpenseViewMixin, LoginRequiredViewMixin, UpdateView):
    form_class = ExpenseForm


class ExpenseDelete(ExpenseViewMixin, LoginRequiredViewMixin, DeleteView):
    pass

