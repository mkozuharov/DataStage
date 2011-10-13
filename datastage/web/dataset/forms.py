from django import forms

DATABANK_CHOICES = (
    ('https://databank.ora.ox.ac.uk/', 'Oxford Research Archive'),
    ('https://test.databank.ox.ac.uk/', 'Test Databank'),
)

class StageOneForm(forms.Form):
    known_databank = forms.MultipleChoiceField(choices=DATABANK_CHOICES, widget=forms.Select)

