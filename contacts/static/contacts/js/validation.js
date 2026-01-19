/**
 * Form Validation Module - Client-side validation for Contact forms
 */

function initFormValidation() {
    const form = document.getElementById('contactForm');
    if (!form) return;

    form.addEventListener('submit', function(event) {
        if (!validateForm()) {
            event.preventDefault();
            event.stopPropagation();
        }
        form.classList.add('was-validated');
    });

    // Real-time validation on blur
    form.querySelectorAll('input, select').forEach(input => {
        input.addEventListener('blur', () => validateField(input));
        input.addEventListener('input', function() {
            if (this.classList.contains('is-invalid')) {
                validateField(this);
            }
        });
    });
}

function validateForm() {
    const fields = ['first_name', 'last_name', 'phone_number', 'email', 'city', 'status'];
    let isValid = true;

    fields.forEach(fieldId => {
        const field = document.getElementById('id_' + fieldId);
        if (field && !validateField(field)) {
            isValid = false;
        }
    });

    return isValid;
}

function validateField(field) {
    if (!field) return true;

    const value = field.value.trim();
    const fieldName = field.id.replace('id_', '');
    let isValid = true;
    let errorMessage = '';

    switch (fieldName) {
        case 'first_name':
        case 'last_name':
            if (!value) {
                isValid = false;
                errorMessage = fieldName === 'first_name' ? 'Imię jest wymagane.' : 'Nazwisko jest wymagane.';
            } else if (value.length < 2) {
                isValid = false;
                errorMessage = 'Minimum 2 znaki.';
            } else if (!/^[a-zA-ZąćęłńóśźżĄĆĘŁŃÓŚŹŻ\s\-]+$/.test(value)) {
                isValid = false;
                errorMessage = 'Tylko litery są dozwolone.';
            }
            break;

        case 'phone_number':
            if (!value) {
                isValid = false;
                errorMessage = 'Numer telefonu jest wymagany.';
            } else if (!/^\+?\d{9,15}$/.test(value.replace(/\s/g, ''))) {
                isValid = false;
                errorMessage = 'Format: +48123456789 (9-15 cyfr).';
            }
            break;

        case 'email':
            if (!value) {
                isValid = false;
                errorMessage = 'E-mail jest wymagany.';
            } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
                isValid = false;
                errorMessage = 'Nieprawidłowy format e-mail.';
            }
            break;

        case 'city':
            if (!value) {
                isValid = false;
                errorMessage = 'Miasto jest wymagane.';
            } else if (value.length < 2) {
                isValid = false;
                errorMessage = 'Minimum 2 znaki.';
            }
            break;

        case 'status':
            if (!value) {
                isValid = false;
                errorMessage = 'Wybierz status.';
            }
            break;
    }

    updateFieldState(field, isValid, errorMessage);
    return isValid;
}

function updateFieldState(field, isValid, errorMessage) {
    const feedback = document.getElementById(field.id.replace('id_', '') + '-error');

    field.classList.toggle('is-valid', isValid);
    field.classList.toggle('is-invalid', !isValid);

    if (feedback && !isValid) {
        feedback.textContent = errorMessage;
    }
}

