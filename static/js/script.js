const typeSelect = document.getElementById("transactionType");
const categorySelect = document.getElementById("categorySelect");

if (typeSelect && categorySelect) {
    typeSelect.addEventListener("change", function () {
        const selectedType = this.value;
        categorySelect.value = "";

        Array.from(categorySelect.options).forEach(option => {
            if (!option.value) {
                option.hidden = false;
                return;
            }

            option.hidden = option.dataset.type !== selectedType;
        });
    });
}