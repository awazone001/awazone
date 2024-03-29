from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import TermsAndConditions, SlidePhoto
from .forms import TermsAndConditionsForms,SlidePhotoForm
from user_module.models import UserProfile, Level
from user_module.decorators import admin_access_only,staff_access_only
from user_module.forms import LevelForm,UserUpdateForm
from messaging_module.models import Notification, ChatRoom
from aibopay.models import AIBORates
from aiboearn.models import Asset,Sector

@login_required
@admin_access_only()
def admin_dashboard(request):
    user_profile = UserProfile.objects.get(email=request.user)
    chats = ChatRoom.objects.filter(is_lock=False)
    sector = Sector.objects.all().order_by('sector')
    asset = Asset.objects.all().order_by('asset')
    context = {
        'user': user_profile,
        'users': UserProfile.objects.exclude(is_staff=True),
        'chats': chats,
        'sectors': sector,
        'assets' :asset, 
    }
    return render(request, 'admin_dashboard.html', context)

@login_required
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
        try:
            termsandconditions_form = TermsAndConditionsForms(instance=TermsAndConditions.objects.latest('last_updated'))
        except TermsAndConditions.DoesNotExist:
            termsandconditions_form = TermsAndConditionsForms()


    context = {'termsandconditions': termsandconditions_form}
    return render(request, 'update_terms_and_conditions.html', context)

@login_required
@admin_access_only()
def view_slides(request):
    slides = SlidePhoto.objects.all()
    content = {
        'slides' : slides
    }
    return render(request,'admin_view_slide.html',content)

@login_required
@admin_access_only()
def create_slide(request):
    slide_form = SlidePhotoForm()
    if request.method=='POST':
        slide_form = SlidePhotoForm(data=request.POST or None, files=request.FILES or None)
        if slide_form.is_valid():
            slide_form.save(commit=True)
            messages.info(request,"Slide has been created successfully")
            return redirect('view_slides')
        else:
            print(slide_form.errors)
    content={"form":slide_form}
    return render(request,'new_slide.html',content)

@login_required
@admin_access_only()
def delete_slide(request,id):
    slide = get_object_or_404(SlidePhoto,pk=id)
    slide.delete()
    return redirect('view_slides',permanent=True)

@login_required
@admin_access_only()
def edit_slide(request,id):
    slide = get_object_or_404(SlidePhoto, pk=id)
    if request.method == 'POST':
        form = SlidePhotoForm(request.POST, request.FILES, instance=slide)
        if form.is_valid():
            if form.cleaned_data['image'] is None: #If no image was uploaded, keep the old one
                form.cleaned_data['image'] = slide.image

            slide.image = form.cleaned_data['image']
            slide.description = form.cleaned_data['description']
            slide.save()
            messages.success(request, "The slide was edited successfully!")
            return redirect('view_slides',permanent=True)
    else:
        form = SlidePhotoForm(instance=slide)
    content ={
       'form' : form,
       'slide' : slide
    }
    return render(request,'new_slide.html',content)






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
