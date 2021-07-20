from django import forms


#class AnnotationForm(forms.Form):
    #image_num = forms.CharField(widget = forms.TextInput({'readonly':'True'}))
    #literal_annotations = forms.CharField(widget = forms.TextInput({'placeholder':'Enter objects (comma-separated) that your see in the image.'}))
    #thematic_annotations = forms.CharField(widget = forms.TextInput({'placeholder': 'Enter themes or concepts (comma-separated) in the image.'}))


class LoginForm(forms.Form):
    username = forms.CharField(widget = forms.TextInput())
    password = forms.CharField(widget = forms.PasswordInput())


class JoinGameForm(forms.Form):
    player_name = forms.CharField()
    # n_players = forms.ChoiceField(choices=[3, 4, 5])

class GameForm(forms.Form):
    img_num = forms.DecimalField()
    clue = forms.CharField(required=False)
    game_num = forms.DecimalField()