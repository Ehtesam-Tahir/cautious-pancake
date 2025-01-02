document.addEventListener("DOMContentLoaded", () => {
    // Object to track selected options across all images
    const selectedOptions = {};

    // Select all image containers
    const imageItems = document.querySelectorAll('.image-item');
    
    // Iterate through each image item to add event listeners for checkboxes
    imageItems.forEach(imageItem => {
        const checkboxes = imageItem.querySelectorAll('input[type="checkbox"]');
        const imageElement = imageItem.querySelector('img');
        const clearButton = document.createElement('button');
        
        // Add "Clear Selection" button for each image item
        clearButton.textContent = "Clear Selection";
        clearButton.classList.add('clear-btn');
        clearButton.style.marginTop = "10px";
        clearButton.style.cursor = "pointer";
        imageItem.appendChild(clearButton);

        // Add hover effect to image when a checkbox is selected
        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', () => {
                const option = checkbox.value;
                const imageId = imageElement.src; // Image URL as identifier

                // If the option is already selected for another image, show alert and uncheck
                if (selectedOptions[option] && selectedOptions[option] !== imageId) {
                    checkbox.checked = false;
                    alert(`Option ${option} is already selected for another image.`);
                } else {
                    // If checked, mark it as selected for the current image
                    if (checkbox.checked) {
                        selectedOptions[option] = imageId;
                    } else {
                        // If unchecked, remove the option from selected options
                        delete selectedOptions[option];
                    }
                }

                // Highlight the selected image with a blue border
                if (checkbox.checked) {
                    imageElement.style.border = "3px solid #1e90ff"; // Blue border
                } else if (![...checkboxes].some(c => c.checked)) {
                    // Remove highlight if no checkbox is selected
                    imageElement.style.border = "none";
                }
            });
        });

        // Clear selection functionality
        clearButton.addEventListener('click', () => {
            checkboxes.forEach(checkbox => checkbox.checked = false);
            imageElement.style.border = "none"; // Remove highlight
        });
    });

    // Form validation to check if the product name is entered before submitting
    const form = document.querySelector('form');
    if (form) {
        form.addEventListener('submit', function (event) {
            const productName = document.getElementById('product_name').value.trim();
            if (!productName) {
                event.preventDefault(); // Stop form submission
                alert('Please enter a product name before submitting.');
            }

            // Ensure at least one checkbox is selected
            const atLeastOneSelected = [...document.querySelectorAll('input[type="checkbox"]')].some(checkbox => checkbox.checked);
            if (!atLeastOneSelected) {
                event.preventDefault();
                alert("Please select at least one checkbox for an image before proceeding!");
            }
        });
    }

    // Grouping and sorting images by base URL (ignores query parameters)
    function getBaseURL(url) {
        return url.split('?')[0]; // Remove query parameters from image URL
    }

    const images = Array.from(document.querySelectorAll('#image-container img'));
    const groups = {};

    images.forEach(img => {
        const baseURL = getBaseURL(img.src);
        if (!groups[baseURL]) {
            groups[baseURL] = [];
        }
        groups[baseURL].push(img);
    });

    // Sort groups by the number of images in each group (descending order)
    const sortedGroups = Object.entries(groups).sort((a, b) => b[1].length - a[1].length);

    // Clear the container before appending sorted images
    const container = document.getElementById('image-container');
    container.innerHTML = '';

    // Append images to the container, with the largest group first
    sortedGroups.forEach(([baseURL, groupImages]) => {
        groupImages.forEach(img => {
            container.appendChild(img); // Append each image from the group to the container
        });
    });
});
