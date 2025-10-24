document.addEventListener('DOMContentLoaded', function() {
    console.log('Payroll form loaded');
    
    // Initialize preview
    updateSalaryPreview();
    
    // Watch salary and deduction fields
    const salaryField = document.getElementById('id_gross_salary');
    if (salaryField) {
        salaryField.addEventListener('input', updateSalaryPreview);
    }
    
    watchDeductionFields();
});

function watchDeductionFields() {
    document.querySelectorAll('.deduction-row input').forEach(field => {
        field.removeEventListener('input', updateSalaryPreview); // Prevent duplicates
        field.addEventListener('input', function() {
            togglePercentageFixed(this);
            updateSalaryPreview();
        });
    });
}

function togglePercentageFixed(field) {
    const row = field.closest('.deduction-row');
    const percentageField = row.querySelector('input[name*="custom_percentage"]');
    const fixedField = row.querySelector('input[name*="fixed_amount"]');
    
    if (field === percentageField && field.value) {
        fixedField.value = '';
    } else if (field === fixedField && field.value) {
        percentageField.value = '';
    }
}

function addDeductionRow() {
    const container = document.getElementById('deduction-container');
    if (!container) {
        console.error('Deduction container not found!');
        return;
    }
    
    let totalFormsInput = document.querySelector('input[name="form-TOTAL_FORMS"]') || 
                         document.querySelector('input[name$="-TOTAL_FORMS"]');
    if (!totalFormsInput) {
        console.error('TOTAL_FORMS input not found!');
        return;
    }
    
    let totalForms = parseInt(totalFormsInput.value) || 1;
    const templateRow = container.querySelector('.deduction-row');
    if (!templateRow) {
        console.error('No template row found!');
        return;
    }
    
    const newRow = templateRow.cloneNode(true);
    newRow.querySelectorAll('input, select').forEach(input => input.value = '');
    
    // Update form indices
    newRow.dataset.formsetIndex = totalForms;
    newRow.querySelectorAll('input, select').forEach(field => {
        let name = field.name;
        if (name) {
            name = name.replace(/form-\d+-/, `form-${totalForms}-`);
            field.name = name;
            field.id = name.replace('form-', 'id_form-');
        }
    });
    
    newRow.querySelectorAll('label').forEach(label => {
        let forAttr = label.getAttribute('for');
        if (forAttr) {
            forAttr = forAttr.replace(/id_form-\d+-/, `id_form-${totalForms}-`);
            label.setAttribute('for', forAttr);
        }
    });
    
    // Show delete button
    const deleteBtn = newRow.querySelector('.btn-outline-danger');
    if (deleteBtn) deleteBtn.style.display = 'inline-block';
    
    container.appendChild(newRow);
    totalFormsInput.value = totalForms + 1;
    
    watchDeductionFields();
    newRow.scrollIntoView({ behavior: 'smooth' });
}

function removeDeductionRow(button) {
    const row = button.closest('.deduction-row');
    const deleteInput = row.querySelector('input[name$="-DELETE"]');
    if (deleteInput) {
        deleteInput.checked = true;
        row.style.opacity = '0.5';
        row.style.pointerEvents = 'none';
    }
    updateSalaryPreview();
}

function updateSalaryPreview() {
    const salaryField = document.getElementById('id_gross_salary');
    if (!salaryField) return;
    
    const salary = parseFloat(salaryField.value) || 0;
    let totalDeductions = 0;
    
    // Mandatory deductions (37.5%)
    if (salary > 0) {
        totalDeductions += salary * 0.0275;
    }
    
    // Optional deductions
    document.querySelectorAll('.deduction-row:not([style*="opacity: 0.5"])').forEach(row => {
        const percentage = parseFloat(row.querySelector('input[name*="custom_percentage"]')?.value) || 0;
        const fixed = parseFloat(row.querySelector('input[name*="fixed_amount"]')?.value) || 0;
        if (percentage > 0) {
            totalDeductions += salary * (percentage / 100);
        } else if (fixed > 0) {
            totalDeductions += fixed;
        }
    });
    
    const netSalary = Math.max(0, salary - totalDeductions);
    
    const grossEl = document.getElementById('gross-preview');
    const deductionsEl = document.getElementById('deductions-preview');
    const netEl = document.getElementById('net-preview');
    
    if (grossEl) grossEl.textContent = salary.toLocaleString('en-KE', { minimumFractionDigits: 2 });
    if (deductionsEl) deductionsEl.textContent = totalDeductions.toLocaleString('en-KE', { minimumFractionDigits: 2 });
    if (netEl) netEl.textContent = netSalary.toLocaleString('en-KE', { minimumFractionDigits: 2 });
}