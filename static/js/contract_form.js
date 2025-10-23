document.addEventListener('DOMContentLoaded', function() {
    // Update preview when salary or deductions change
    document.getElementById('id_salary').addEventListener('input', updatePreview);
    
    // Watch all deduction fields
    document.querySelectorAll('input[name*="custom_percentage"], input[name*="fixed_amount"]').forEach(field => {
        field.addEventListener('input', updatePreview);
    });
});

function updatePreview() {
    const salary = parseFloat(document.getElementById('id_salary').value) || 0;
    let deductions = 0;
    
    // Mandatory deductions (37.5%)
    deductions += salary * 0.375;
    
    // Optional deductions
    document.querySelectorAll('input[name*="custom_percentage"]').forEach(field => {
        if (field.value) deductions += salary * (parseFloat(field.value) / 100);
    });
    
    document.querySelectorAll('input[name*="fixed_amount"]').forEach(field => {
        if (field.value) deductions += parseFloat(field.value);
    });
    
    const net = salary - deductions;
    
    document.getElementById('gross').textContent = salary.toLocaleString();
    document.getElementById('deductions').textContent = deductions.toLocaleString();
    document.getElementById('net').textContent = net.toLocaleString();
}

function addDeductionRow() {
    // Simple add - handled by formset extra forms
    document.querySelector('.formset-row:last-child').scrollIntoView();
}