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
from datastage.web.dataset.models import Repository, DatasetSubmission

DATABANK_CHOICES = (
    ('https://databank.ora.ox.ac.uk/', 'Oxford Research Archive'),
    ('https://test.databank.ox.ac.uk/', 'Test Databank'),
)

class StageOneForm(forms.Form):
    known_databank = forms.MultipleChoiceField(choices=DATABANK_CHOICES, widget=forms.Select)

class DatasetSubmissionForm(forms.ModelForm):
    identifier = forms.CharField()
    title = forms.CharField()
    silo =  forms.ModelChoiceField(queryset=Repository.objects.all())
    #silo = forms.ChoiceField(choices=[(x, x) for x in range(1,5)]
    #opener = openers.get_opener(repository, request.user)
    #silo = forms.ChoiceField(queryset=dataset.obtain_silos(opener, repository))
    
    class Meta:
        model = DatasetSubmission
        fields = ('repository','silo','identifier', 'title', 'description')
    
class SimpleCredentialsForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    next = forms.CharField(widget=forms.HiddenInput)