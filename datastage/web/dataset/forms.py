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
    class Meta:
        model = DatasetSubmission
        fields = ('repository', 'identifier', 'title', 'description')
    
class SimpleCredentialsForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField()
    next = forms.CharField(widget=forms.HiddenInput)