from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import TermsAndConditions, SlidePhoto
from .forms import TermsAndConditionsForms
from user_module.models import UserProfile, Level
from user_module.decorators import admin_access_only,staff_access_only
from user_module.forms import LevelForm,UserUpdateForm
from messaging_module.models import Notification, ChatRoom
from aibopay.models import AIBORates
# from rest_framework import generics, status
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.response import Response
# from user_m.serializers import SlidePhotoSerializer
# from user_management.permissions import IsAdminOrReadOnly

@login_required
@admin_access_only()
def admin_dashboard(request):
    user_profile = UserProfile.objects.get(id=request.user.id)
    chats = ChatRoom.objects.filter(is_lock=False)
    context = {
        'user': user_profile,
        'users': UserProfile.objects.exclude(is_staff=True),
        'chats': chats
    }
    return render(request, 'admin_dashboard.html', context)


@login_required
@staff_access_only()
def staff_dashboard(request):
    return render(request,'staff_dashboard.html')

@login_required(login_url='user_login')
@admin_access_only()
def view_staffs(request):
    user_profile = UserProfile.objects.get(email=request.user.email)
    context = {
        'user': user_profile,
        'users': UserProfile.objects.exclude(is_staff=True),
        'staff': UserProfile.objects.exclude(is_user=True)
    }
    return render(request, 'staffs.html', context)

@login_required
@admin_access_only()
def update_profile(request):
    user = UserProfile.objects.get(email=request.user.email)
    update_form = UserUpdateForm(request.POST, request.FILES)
    try:
        if request.method == 'POST':
            update_form = UserUpdateForm(request.POST, request.FILES)
            if update_form.is_valid():
                user.profile_image = update_form.cleaned_data['profile_image']
                user.phone_number = update_form.cleaned_data['phone_number']
                user.save() 
                messages.info(request, 'User Details Updated!')
                return redirect('user_profile')
            else:
                user.profile_image = update_form.cleaned_data['profile_image']
                user.phone_number = update_form.cleaned_data['phone_number']
                user.save()
                messages.info(request, 'User Details Updated!')
                return redirect('user_profile')
    except Exception as e:
        messages.error(request, f'Error Occurred: {e}')
    content = {
        'user': user,
        'update_form': update_form,
    }
    return render(request, 'admin_profile.html', content)

@login_required(login_url='user_login')
@admin_access_only()
def view_staff(request, id):
    searched_user = get_object_or_404(UserProfile, id=id)
    context = {
        'user': searched_user,
        'users': UserProfile.objects.exclude(is_staff=True),
        'staff': UserProfile.objects.exclude(is_user=True)
    }
    return render(request, 'admin/user.html', context)

@login_required(login_url='user_login')
@admin_access_only()
def manage_terms_and_conditions(request):
    if request.method == 'POST':
        termsandconditions_form = TermsAndConditionsForms(request.POST)
        if termsandconditions_form.is_valid():
            termsandconditions_form.save()
            messages.success(request, 'Terms and Conditions Updated Successfully!')
            return redirect('manage_terms_and_conditions')
        else:
            messages.error(request, 'Invalid Forms')
    else:
        termsandconditions_form = TermsAndConditionsForms(instance=TermsAndConditions.objects.get_or_create(id='4Awazone-licenses')[0])

    context = {'termsandconditions': termsandconditions_form}
    return render(request, 'update_terms_and_conditions.html', context)

@login_required(login_url='user_login')
@admin_access_only()
def admin_view_level(request):
    context = {
        'levels': Level.objects.all().order_by('level'),
        'users': UserProfile.objects.exclude(is_staff=False),
        'staff': UserProfile.objects.exclude(is_staff=True)
    }
    return render(request, 'admin_view_rank.html', context)

@login_required(login_url='user_login')
@admin_access_only()
def add_level(request):
    if request.method == 'POST':
        new_level_form = LevelForm(request.POST)
        if new_level_form.is_valid():
            new_level_form.save()
            messages.success(request, 'New Level Successfully Added!')
            return redirect('admin_view_level')
        else:
            messages.error(request, 'Invalid Inputs')
    else:
        new_level_form = LevelForm()

    context = {
        'form': new_level_form,
        'users': UserProfile.objects.exclude(is_staff=False),
        'staff': UserProfile.objects.exclude(is_staff=True)
    }
    return render(request, 'admin_update_rank.html', context)



# class SlidePhotoListCreateAPIView(generics.ListCreateAPIView):
#     queryset = SlidePhoto.objects.all()
#     serializer_class = SlidePhotoSerializer
#     permission_classes = [IsAuthenticated]

# class SlidePhotoRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
#     queryset = SlidePhoto.objects.all()
#     serializer_class = SlidePhotoSerializer
#     permission_classes = [IsAdminOrReadOnly]

#     def update(self, request, *args, **kwargs):
#         instance = self.get_object()
#         serializer = self.get_serializer(instance, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)

#     def destroy(self, request, *args, **kwargs):
#         instance = self.get_object()
#         self.perform_destroy(instance)
#         return Response(status=status.HTTP_204_NO_CONTENT)
