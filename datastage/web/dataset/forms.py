# ---------------------------------------------------------------------
#
# Copyright (c) 2012 University of Oxford
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, --INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# 
# ---------------------------------------------------------------------

from django import forms
from django.forms import ModelForm, Textarea
from datastage.web.dataset.models import Repository, DatasetSubmission, DefaultRepository
from django.shortcuts import get_object_or_404
DATABANK_CHOICES = (
    ('https://databank.ora.ox.ac.uk/', 'Oxford Research Archive'),
    ('https://test.databank.ox.ac.uk/', 'Test Databank'),
)

class StageOneForm(forms.Form):
    known_databank = forms.MultipleChoiceField(choices=DATABANK_CHOICES, widget=forms.Select)

#class DefaultRepositoryForm(forms.Form):
#    defaultrepository = get_object_or_404(Repository, id=DefaultRepository.objects.all()[0].repository_id)
    #defaultrepositoryfield = forms.CharField(initial=defaultrepository ,widget=forms.HiddenInput)
    

#from django.utils.html import format_html 
#from django.utils.encoding import force_text 
#from django.forms.util import flatatt
#
#class DefaultTextarea(forms.Textarea):
##    def set_default(self, default=""):
##        self.DEFAULT = default
##        
#    def render(self, name, value, attrs=None):
#        if value is None: value = 'JKGKJG'
#        final_attrs = self.build_attrs(attrs, name=name)
#        return format_html('<textarea{0}>\r\n{1}</textarea>',
#                           flatatt(final_attrs),
#                           force_text(value))

class DatasetSubmissionForm(forms.ModelForm):
    identifier = forms.CharField()
    title = forms.CharField()
    #defaultrepository = get_object_or_404(Repository, id=DefaultRepository.objects.all()[0].repository_id)
	    defrepos = DefaultRepository.objects.all()
    if defrepos:
      defaultrepository = get_object_or_404(Repository, id=defrepos[0].repository_id)
    else:
      defaultrepository = None
    #repository = forms.CharField(initial=defaultrepository,widget=forms.HiddenInput())
    repository =  forms.ModelChoiceField(queryset=Repository.objects.all(),widget=forms.HiddenInput())
    license = forms.CharField(widget=forms.Textarea, required= False)
    #license = DefaultTextarea()
    #license.set_default("this is def val")
# )
    #repo = get_object_or_404(Repository, id=DefaultRepository.objects.all()[0].repository_id)
    #defaultrepository = forms.CharField(label='Default Repository',initial='aaaa')
    #silo = forms.ChoiceField(choices=[(x, x) for x in range(1,5)])
    #SILO_CHOICES =  [('sandbox','sandbox'), ('datastage','datastage'), ('softwarestore','softwarestore')]
    #silo = forms.ChoiceField(choices=SILO_CHOICES)
    #opener = openers.get_opener(repository, request.user)
    #silo = forms.ChoiceField(queryset=dataset.obtain_silos(opener, repository))
    
    class Meta:
        model = DatasetSubmission
        fields = ('repository','identifier', 'title', 'description','license')
#        key = 'license'
#        for key in fields:
#            fields[key].required = False
        #widgets = { 'license' :  Textarea(attrs={'label':'License','initial':'aaaa'}), }  
        
class SimpleCredentialsForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    next = forms.CharField(widget=forms.HiddenInput)