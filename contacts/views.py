import csv
import io
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
)
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect

from .models import Contact, ContactStatusChoices
from .forms import ContactForm, ContactImportForm


class ContactListView(ListView):
    """Display paginated list of contacts with search and sorting."""

    model = Contact
    template_name = 'contacts/contact_list.html'
    context_object_name = 'contacts'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()

        search_query = self.request.GET.get('q', '').strip()
        sort_by = self.request.GET.get('sort', 'date_added')
        sort_order = self.request.GET.get('order', 'desc')
        status_filter = self.request.GET.get('status', '')

        # Search filter
        if search_query:
            queryset = queryset.filter(
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(city__icontains=search_query) |
                Q(phone_number__icontains=search_query)
            )

        # Status filter
        if status_filter:
            queryset = queryset.filter(status_id=status_filter)

        # Sorting
        valid_sort_fields = ['last_name', 'date_added', 'first_name', 'city']
        if sort_by not in valid_sort_fields:
            sort_by = 'date_added'

        order_prefix = '-' if sort_order == 'desc' else ''
        queryset = queryset.order_by(f'{order_prefix}{sort_by}')

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_query'] = self.request.GET.get('q', '')
        context['sort_by'] = self.request.GET.get('sort', 'date_added')
        context['sort_order'] = self.request.GET.get('order', 'desc')
        context['selected_status'] = self.request.GET.get('status', '')
        context['statuses'] = ContactStatusChoices.objects.all()
        context['total_contacts'] = Contact.objects.count()
        return context


class ContactDetailView(DetailView):
    """Display single contact details."""

    model = Contact
    template_name = 'contacts/contact_detail.html'
    context_object_name = 'contact'


class ContactCreateView(CreateView):
    """Handle new contact creation."""

    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'
    success_url = reverse_lazy('contacts:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Dodaj nowy kontakt'
        context['button_text'] = 'Dodaj kontakt'
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Kontakt "{form.instance.first_name} {form.instance.last_name}" został dodany!'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Wystąpiły błędy w formularzu.')
        return super().form_invalid(form)


class ContactUpdateView(UpdateView):
    """Handle contact editing."""

    model = Contact
    form_class = ContactForm
    template_name = 'contacts/contact_form.html'
    success_url = reverse_lazy('contacts:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edytuj kontakt: {self.object}'
        context['button_text'] = 'Zapisz zmiany'
        context['is_edit'] = True
        return context

    def form_valid(self, form):
        messages.success(
            self.request,
            f'Kontakt "{form.instance.first_name} {form.instance.last_name}" został zaktualizowany!'
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Wystąpiły błędy w formularzu.')
        return super().form_invalid(form)


class ContactDeleteView(DeleteView):
    """Handle contact deletion with confirmation."""

    model = Contact
    template_name = 'contacts/contact_confirm_delete.html'
    success_url = reverse_lazy('contacts:list')
    context_object_name = 'contact'

    def form_valid(self, form):
        contact_name = f"{self.object.first_name} {self.object.last_name}"
        messages.success(self.request, f'Kontakt "{contact_name}" został usunięty!')
        return super().form_valid(form)


class ContactImportView(FormView):
    """Handle CSV file import for bulk contact creation."""

    template_name = 'contacts/contact_import.html'
    form_class = ContactImportForm
    success_url = reverse_lazy('contacts:list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['csv_columns'] = ['first_name', 'last_name', 'phone_number', 'email', 'city', 'status']
        return context

    def form_valid(self, form):
        csv_file = form.cleaned_data['csv_file']

        # Decode file content
        try:
            decoded_file = csv_file.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                csv_file.seek(0)
                decoded_file = csv_file.read().decode('latin-1')
            except Exception:
                messages.error(self.request, 'Nie można odczytać pliku.')
                return self.form_invalid(form)

        # Parse CSV with auto-detected delimiter
        io_string = io.StringIO(decoded_file)
        try:
            sample = decoded_file[:1024]
            dialect = csv.Sniffer().sniff(sample, delimiters=',;')
            io_string.seek(0)
            reader = csv.DictReader(io_string, dialect=dialect)
        except csv.Error:
            io_string.seek(0)
            reader = csv.DictReader(io_string)

        # Validate required columns
        required_columns = {'first_name', 'last_name', 'phone_number', 'email', 'city', 'status'}
        if not reader.fieldnames:
            messages.error(self.request, 'Plik CSV jest pusty lub ma nieprawidłowy format.')
            return self.form_invalid(form)

        headers = {h.strip().lower() for h in reader.fieldnames if h}
        missing_columns = required_columns - headers
        if missing_columns:
            messages.error(self.request, f'Brakujące kolumny: {", ".join(missing_columns)}')
            return self.form_invalid(form)

        # Process rows
        created_count = 0
        skipped_count = 0

        default_status, _ = ContactStatusChoices.objects.get_or_create(
            name='nowy',
            defaults={'description': 'Nowy kontakt'}
        )

        for row in reader:
            try:
                row = {k.strip().lower(): v.strip() if v else '' for k, v in row.items() if k}

                if not any(row.values()):
                    continue

                # Get status or use default
                status_name = row.get('status', '').strip()
                try:
                    status = ContactStatusChoices.objects.get(name__iexact=status_name)
                except ContactStatusChoices.DoesNotExist:
                    status = default_status

                # Check for duplicates
                email = row.get('email', '').lower()
                phone = row.get('phone_number', '')

                if Contact.objects.filter(email=email).exists():
                    skipped_count += 1
                    continue

                if Contact.objects.filter(phone_number=phone).exists():
                    skipped_count += 1
                    continue

                # Create contact
                Contact.objects.create(
                    first_name=row.get('first_name', '').title(),
                    last_name=row.get('last_name', '').title(),
                    phone_number=phone,
                    email=email,
                    city=row.get('city', '').title(),
                    status=status
                )
                created_count += 1

            except Exception:
                skipped_count += 1

        if created_count > 0:
            messages.success(self.request, f'Zaimportowano {created_count} kontakt(ów).')
        if skipped_count > 0:
            messages.warning(self.request, f'Pominięto {skipped_count} wiersz(y).')

        return HttpResponseRedirect(self.success_url)
