document.addEventListener('DOMContentLoaded', function() {
    console.log('Contract form loaded');
    
    // Initialize preview
    updateSalaryPreview();
    
    // Watch salary field
    const salaryField = document.getElementById('id_salary');
    if (salaryField) {
        salaryField.addEventListener('input', updateSalaryPreview);
    }
    
    // Watch existing deduction fields
    watchExistingDeductionFields();
});

function watchExistingDeductionFields() {
    document.querySelectorAll('.deduction-row input').forEach(field => {
        field.addEventListener('input', updateSalaryPreview);
    });
}

function addDeductionRow() {
    console.log('Add button clicked');
    
    // SAFEGUARD: Check if container exists
    const container = document.getElementById('deduction-container');
    if (!container) {
        console.error('Deduction container not found!');
        return;
    }
    
    // SAFEGUARD: Get TOTAL_FORMS safely
    let totalFormsInput = document.querySelector('input[name="deduction_set-TOTAL_FORMS"]') || 
                         document.querySelector('input[name$="-TOTAL_FORMS"]');
    
    if (!totalFormsInput) {
        console.error('TOTAL_FORMS input not found!');
        return;
    }
    
    let totalForms = parseInt(totalFormsInput.value) || 1;
    
    // Clone FIRST row as template
    const templateRow = container.querySelector('.deduction-row');
    if (!templateRow) {
        console.error('No template row found!');
        return;
    }
    
    const newRow = templateRow.cloneNode(true);
    
    // Clear all values in new row
    newRow.querySelectorAll('input, select').forEach(input => {
        input.value = '';
    });
    
    // Update ALL form indices
    updateFormIndices(newRow, totalForms);
    
    // Show delete button
    const deleteBtn = newRow.querySelector('.btn-outline-danger');
    if (deleteBtn) {
        deleteBtn.style.display = 'inline-block';
    }
    
    // Append new row
    container.appendChild(newRow);
    
    // Update counter
    totalFormsInput.value = totalForms + 1;
    
    // Re-attach event listeners to ALL rows
    watchAllDeductionFields();
    
    // Scroll to new row
    newRow.scrollIntoView({ behavior: 'smooth' });
    
    console.log('New row added. Total forms:', totalForms + 1);
}

function updateFormIndices(row, newIndex) {
    row.querySelectorAll('input, select').forEach(field => {
        // Update name
        let name = field.name;
        if (name) {
            name = name.replace(/deduction_set-\d+-/, `deduction_set-${newIndex}-`);
            field.name = name;
        }
        
        // Update id
        let id = field.id;
        if (id) {
            id = id.replace(/id_deduction_set-\d+-/, `id_deduction_set-${newIndex}-`);
            field.id = id;
        }
    });
    
    // Update labels
    row.querySelectorAll('label').forEach(label => {
        let forAttr = label.getAttribute('for');
        if (forAttr) {
            forAttr = forAttr.replace(/id_deduction_set-\d+-/, `id_deduction_set-${newIndex}-`);
            label.setAttribute('for', forAttr);
        }
    });
}

function removeDeductionRow(button) {
    const row = button.closest('.deduction-row');
    const deleteInput = row.querySelector('input[name$="-DELETE"]');
    
    if (deleteInput) {
        deleteInput.checked = true;
        row.style.opacity = '0.5';
        row.style.pointerEvents = 'none';
    }
}

function watchAllDeductionFields() {
    document.querySelectorAll('.deduction-row input').forEach(field => {
        field.removeEventListener('input', updateSalaryPreview); // Prevent duplicates
        field.addEventListener('input', updateSalaryPreview);
    });
}

function togglePercentageFixed(field) {
    const row = field.closest('.deduction-row');
    const percentageField = row.querySelector('input[name*="custom_percentage"]');
    const fixedField = row.querySelector('input[name*="fixed_amount"]');
    
    if (!percentageField || !fixedField) return;
    
    if (field === percentageField && field.value) {
        fixedField.value = '';
    } else if (field === fixedField && field.value) {
        percentageField.value = '';
    }
}

function updateSalaryPreview() {
    const salaryField = document.getElementById('id_salary');
    if (!salaryField) return;
    
    const salary = parseFloat(salaryField.value) || 0;
    let totalDeductions = 0;
    
    // Mandatory deductions (37.5%)
    if (salary > 0) {
        totalDeductions += salary * 0.375;
    }
    
    // Optional deductions from ACTIVE rows only
    document.querySelectorAll('.deduction-row').forEach(row => {
        if (row.style.opacity !== '0.5') { // Not deleted
            const percentage = parseFloat(row.querySelector('input[name*="custom_percentage"]')?.value) || 0;
            const fixed = parseFloat(row.querySelector('input[name*="fixed_amount"]')?.value) || 0;
            
            if (percentage > 0) {
                totalDeductions += salary * (percentage / 100);
            } else if (fixed > 0) {
                totalDeductions += fixed;
            }
        }
    });
    
    const netSalary = Math.max(0, salary - totalDeductions);
    
    // SAFEGUARD: Check elements exist
    const grossEl = document.getElementById('gross-salary');
    const deductionsEl = document.getElementById('total-deductions');
    const netEl = document.getElementById('net-salary');
    
    if (grossEl) grossEl.textContent = salary.toLocaleString('en-KE', { minimumFractionDigits: 2 });
    if (deductionsEl) deductionsEl.textContent = totalDeductions.toLocaleString('en-KE', { minimumFractionDigits: 2 });
    if (netEl) netEl.textContent = netSalary.toLocaleString('en-KE', { minimumFractionDigits: 2 });
}