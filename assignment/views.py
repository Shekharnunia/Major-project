from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.contenttypes.models import ContentType
from django.shortcuts import reverse, get_object_or_404, render, redirect
from django.views.generic import (
    ListView,
    DeleteView,
    UpdateView,
    DetailView,
    CreateView,
)

from helpers import AuthorRequiredMixin, TeacherRequiredMixin
from .models import Assignment, StudentAssignment
from .forms import AssignmentForm, StudentAssignmentForm
from comments.forms import CommentForm
from comments.models import Comment


class AllAssignmentListView(LoginRequiredMixin, ListView):
    model = Assignment
    paginate_by = 10
    context_object_name = 'assignments'

    def get_queryset(self):
        assignemt = Assignment.objects.get_assignment()
        all_assignemt = Assignment.objects.all().filter(uploader=self.request.user)
        union = all_assignemt.union(assignemt).order_by('-timestamp')
        return union

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["popular_tags"] = Assignment.objects.get_counted_tags()
        context["active"] = "all"
        return context


class AssignmentListView(AllAssignmentListView):

    def get_queryset(self):
        return Assignment.objects.get_assignment().order_by('-timestamp')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["active"] = "assignment"
        return context


class AssignmentDraftListView(TeacherRequiredMixin, AllAssignmentListView):

    def get_queryset(self):
        return Assignment.objects.get_draft_assignment().filter(uploader=self.request.user).order_by('-timestamp')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["active"] = "draft"
        return context


class AssignmentOldestListView(AllAssignmentListView):

    def get_queryset(self):
        return Assignment.objects.get_oldest_student().order_by('-timestamp')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["active"] = "oldest"
        return context


class AssignmentNewestListView(AllAssignmentListView):

    def get_queryset(self):
        return Assignment.objects.get_newest_student().order_by('-timestamp')

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["active"] = "newest"
        return context


class TagAssignmentListView(AllAssignmentListView):
    """Overriding the original implementation to call the tag question
    list."""

    def get_queryset(self, **kwargs):
        return Assignment.objects.filter(tags__name=self.kwargs['tag_name']).order_by('-timestamp')


class AssignmentDetailView(LoginRequiredMixin, DetailView):
    model = Assignment
    context_object_name = 'assignment'

    def get_context_data(self, **kwargs):
        session_key = 'viewed_assignment_{}'.format(self.object.pk)
        if not self.request.session.get(session_key, False):
            self.object.assignment_views += 1
            self.object.save()
            self.request.session[session_key] = True
        return super().get_context_data(**kwargs)


@login_required
def assignment_detail_view(request, pk, slug):
    form = StudentAssignmentForm(request.POST, request.FILES)
    t_assignment = get_object_or_404(Assignment, pk=pk)

    session_key = 'viewed_assignment_{}'.format(t_assignment.pk)
    if not request.session.get(session_key, False):
        t_assignment.assignment_views += 1
        t_assignment.save()
        request.session[session_key] = True
    if request.user.is_student == True:
        s_assignment = StudentAssignment.objects.filter(assignment=t_assignment).filter(user=request.user).order_by('-timestamp')
    elif request.user.is_teacher:
        s_assignment = StudentAssignment.objects.filter(assignment=t_assignment).order_by('-timestamp')

    initial_data = {
        "content_type": t_assignment.get_content_type,
        "object_id": t_assignment.id
    }
    comment_form = CommentForm(request.POST or None, initial=initial_data)

    if request.method == 'POST':
        if form.is_valid() and request.user.is_student:
            s_assignment = form.save(commit=False)
            s_assignment.assignment = t_assignment
            s_assignment.user = request.user
            s_assignment = form.save()

            messages.success(request, 'assignment successfully submitted')
            return redirect(s_assignment.get_absolute_url())

        if comment_form.is_valid():
            c_type = comment_form.cleaned_data.get("content_type")
            content_type = ContentType.objects.get(model=c_type)
            obj_id = comment_form.cleaned_data.get('object_id')
            content_data = comment_form.cleaned_data.get("content")
            parent_obj = None
            try:
                parent_id = int(request.POST.get("parent_id"))
            except:
                parent_id = None

            if parent_id:
                parent_qs = Comment.objects.filter(id=parent_id)
                if parent_qs.exists() and parent_qs.count() == 1:
                    parent_obj = parent_qs.first()

            new_comment, created = Comment.objects.get_or_create(
                user=request.user,
                content_type=content_type,
                object_id=obj_id,
                content=content_data,
                parent=parent_obj,
            )
            return redirect(new_comment.content_object.get_absolute_url())
    form = StudentAssignmentForm
    comments = t_assignment.comments
    args = {
        'assignment': t_assignment,
        's_form': form,
        's_assignments': s_assignment,
        "comments": comments,
        "comment_form": comment_form,
    }
    return render(request, 'assignment/assignment_detail.html', args)


class StudentAssignmentEditView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = StudentAssignment
    form_class = StudentAssignmentForm
    template_name = 'assignment/edit_assignment.html'
    pk_url_kwarg = 'pk'
    context_object_name = 'assignment'
    message = ("assignment successfully updated")

    def get_success_url(self):
        assignment = self.get_object()
        messages.success(self.request, self.message)
        return reverse('assignment:detail',
                       kwargs={'pk': assignment.assignment.pk,
                               'slug': assignment.assignment.slug})

    def test_func(self):
        assignment = self.get_object()
        if self.request.user == assignment.user:
            return True
        return False


class StudentAssignmentDeleteView(LoginRequiredMixin, AuthorRequiredMixin, DeleteView):
    """Basic EditView implementation to edit existing articles."""
    model = StudentAssignment
    message = ("Your article has been deleted.")
    context_object_name = 'assignment'
    pk_url_kwarg = 'pk'

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        assignment = self.get_object()
        messages.success(self.request, self.message)
        return reverse('assignment:detail',
                       kwargs={'pk': assignment.assignment.pk,
                               'slug': assignment.assignment.slug})


class AssignmentCreateView(LoginRequiredMixin, TeacherRequiredMixin, CreateView):
    model = Assignment
    form_class = AssignmentForm
    template_name = 'assignment/assignment_create.html'
    message = ("Your Assignment has been created.")

    def form_valid(self, form):
        form.instance.uploader = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, self.message)
        return reverse("assignment:all_list")


class AssignmentEditView(LoginRequiredMixin, UserPassesTestMixin, TeacherRequiredMixin, UpdateView):
    model = Assignment
    context_object_name = 'assignment'
    fields = ('topic', 'description', 'assignment_file', 'tags',)
    message = ("assignment successfully updated")

    def get_success_url(self):
        assignment = self.get_object()
        messages.success(self.request, self.message)
        return reverse('assignment:detail',
                       kwargs={'pk': assignment.pk,
                               'slug': assignment.slug})


class AssignmentDeleteView(LoginRequiredMixin, UserPassesTestMixin, TeacherRequiredMixin, DeleteView):
    model = Assignment
    context_object_name = 'assignment'
    message = ("Your article has been deleted.")

    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        messages.success(self.request, self.message)
        return reverse('assignment:list')

    def test_func(self):
        assignment = self.get_object()
        if self.request.user == assignment.uploader:
            return True
        return False
