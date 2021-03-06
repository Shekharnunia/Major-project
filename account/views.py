from django.core.exceptions import PermissionDenied

from django.contrib import messages
from django.contrib.auth import(authenticate,get_user_model,login,logout)
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required

from django.db import transaction
from django.forms.models import inlineformset_factory

from django.shortcuts import render, redirect
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.generic import UpdateView, CreateView, DetailView

from account.forms import RegistrationForm, UserProfileForm
from account.models import UserProfile


def register(request):
    if not request.user.is_authenticated:    
        if request.method =='POST':
            form = RegistrationForm(request.POST )
            if form.is_valid():
                user = form.save()
                user.refresh_from_db()
                user.user.role = form.cleaned_data.get('role')
                user.save()
                username = form.cleaned_data.get('username')
                raw_password = form.cleaned_data.get('password1')
                user = authenticate(username=username, password=raw_password)
                login(request, user)
                messages.success(request, 'Your account successfully created')
                return redirect(('main:home'))
        else:
            form = RegistrationForm()
        return render(request, 'account/register.html',{'form': form})
    else:
        return redirect(reverse('qa:index_noans'))


@login_required
def profile(request, username):
    user = User.objects.get(username=username)
    return render(request, 'account/profile.html', {"user":user})


@login_required
def edit_user(request, pk):
    user = User.objects.get(pk=pk)
    user_form = UserProfileForm(instance=user)

    ProfileInlineFormset = inlineformset_factory(User, UserProfile, fields=('website', 'bio', 'phone', 'city', 'country', 'organization', 'birthdate', 'image'))
    formset = ProfileInlineFormset(instance=user)

    if request.user.is_authenticated and request.user.id == user.id:
        if request.method == "POST":
            user_form = UserProfileForm(request.POST, request.FILES, instance=user)
            formset = ProfileInlineFormset(request.POST, request.FILES, instance=user)

            if user_form.is_valid():
                created_user = user_form.save(commit=False)
                formset = ProfileInlineFormset(request.POST, request.FILES, instance=created_user)

                if formset.is_valid():
                    created_user.save()
                    formset.save()
                    messages.success(request, 'Profile details updated.')
                    return redirect('account:profile', username=user.username)

        return render(request, "account/account_update.html", {
            "noodle": pk,
            "form": user_form,
            "formset": formset,
        })
    else:
        raise PermissionDenied



# def login_view(request):
#     if request.user.is_authenticated: 
#         return redirect('main:home')
#     if request.method == "POST":
#         username=request.POST.get('username')
#         password=request.POST.get('password')
        
#         user=authenticate(username=username,password=password)
#         try:
#             login(request,user)
#             return redirect('main:home')
#         except:
#             return redirect('account:register')

#     return render(request,'account/Login_v1/index.html',{})



# @method_decorator(login_required, name='dispatch')
# class UserUpdateView(UpdateView):
#     model = User
#     fields = ('first_name', 'last_name', 'email', )
#     template_name = 'account/edit_profile.html'

#     def form_valid(self, form):
#         profile_obj = form.save(commit=False)
#         profile_obj.save()
#         messages.success(self.request, 'Profile details updated.')
#         return redirect('account:profile', username=profile_obj.username)

#     def get_object(self):
#         return self.request.user
