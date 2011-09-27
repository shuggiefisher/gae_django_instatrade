
from django import forms
from django.template import RequestContext
from django.shortcuts import render_to_response, redirect

from manytomany.models import *


def products(request):
    data = {}
    if (request.POST):
        form = ProductForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            description = form.cleaned_data['description']
            product = Product(name=name, description=description)
            product.save()
            return redirect('/products/')
        else:
            data['form'] = form
    else:
        data['form'] = ProductForm()

    data['products'] = Product.objects.all()
    return render_to_response('products.html', data, 
                              context_instance=RequestContext(request))


def companies(request):
    data = {}
    if (request.POST):
        form = CompanyForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            tagline = form.cleaned_data['tagline']
            company = Company(name=name, tagline=tagline)
            company.save()
            return redirect('/companies/')
        else:
            data['form'] = form
    else:
        data['form'] = CompanyForm()

    data['companies'] = Company.objects.all()
    return render_to_response('companies.html', data, 
                              context_instance=RequestContext(request))


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        
class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company

