# -*- coding: utf-8 -*-

from django import forms
from django.forms.extras.widgets import SelectDateWidget
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import widgets             

from topfuns.models import Report                          

class AdminReportForm(forms.Form):
    beginWith = forms.DateField(('%d.%m.%Y',), label=_("Begin with:"), 
                    required=True, widget=widgets.AdminDateWidget())
    endWith = forms.DateField(('%d.%m.%Y',), label=_("End with"), 
                required=True, widget=widgets.AdminDateWidget())
                
class DownloadReportForm(forms.Form):
    
    def __init__(self, *args, **kwargs):
        self.reports = kwargs['reports']
        del kwargs['reports']
        
        super(DownloadReportForm, self).__init__(*args, **kwargs)
        
        choices = []
        for report in self.reports:      
            choices.append((report.id, '%s - %s' % (report.start.strftime('%d.%m.%Y'), report.end.strftime('%d.%m.%Y'))))
            
        self.fields['report'] = forms.ChoiceField(widget=forms.RadioSelect, required=True, choices=choices, label=_('Reports'))
        
    def clean_report(self):
        try:
            report_id = int(self.cleaned_data.get('report'))
        except IndexError:
            raise forms.ValidationError, 'Report must be integer'
        
        try:
            report = self.reports.get(id=report_id)
        except Report.DoesNotExist:
            raise forms.ValidationError, "Report does not exist"
            
        return self.cleaned_data.get('report')      
        
    def get_report(self):
        return Report.objects.get(id=int(self.cleaned_data.get('report')))
