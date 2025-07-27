class StarRating {
    constructor(element) {
        this.element = element;
        this.stars = element.querySelectorAll('.star');
        this.rating = 0;
        this.init();
    }

    init() {
        this.stars.forEach((star, index) => {
            star.addEventListener('click', () => this.setRating(index + 1));
            star.addEventListener('mouseover', () => this.highlightStars(index + 1));
            star.addEventListener('mouseout', () => this.resetStars());
        });
    }

    setRating(rating) {
        this.rating = rating;
        document.getElementById('rating-value').value = rating;
        this.highlightStars(rating);
    }

    highlightStars(count) {
        this.stars.forEach((star, index) => {
            star.classList.toggle('active', index < count);
        });
    }

    resetStars() {
        this.highlightStars(this.rating);
    }
}

// Recipe Scaling
function scaleRecipe(factor) {
    const ingredients = document.querySelectorAll('.ingredient-amount');
    ingredients.forEach(ingredient => {
        const originalAmount = parseFloat(ingredient.dataset.original);
        if (!isNaN(originalAmount)) {
            ingredient.textContent = (originalAmount * factor).toFixed(2);
        }
    });
}

// Shopping List Generation
function addToShoppingList(recipeId) {
    const ingredients = document.querySelectorAll('.ingredient-item');
    const list = [];
    ingredients.forEach(item => {
        list.push({
            name: item.dataset.name,
            amount: item.dataset.amount,
            unit: item.dataset.unit
        });
    });
    localStorage.setItem(`shopping-list-${recipeId}`, JSON.stringify(list));
}

// Print Recipe
function printRecipe() {
    window.print();
}

// Social Media Sharing
function shareRecipe(platform, url, title) {
    const shareUrls = {
        facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(url)}`,
        twitter: `https://twitter.com/intent/tweet?url=${encodeURIComponent(url)}&text=${encodeURIComponent(title)}`,
        pinterest: `https://pinterest.com/pin/create/button/?url=${encodeURIComponent(url)}&description=${encodeURIComponent(title)}`
    };
    window.open(shareUrls[platform], 'share', 'width=600,height=400');
}

// Form Validation
function validateRecipeForm() {
    const title = document.getElementById('recipe-title').value;
    const instructions = tinymce.get('recipe-instructions').getContent();
    const ingredients = document.querySelectorAll('.ingredient-row');
    
    if (!title.trim()) {
        alert('Please enter a recipe title');
        return false;
    }
    
    if (!instructions.trim()) {
        alert('Please enter recipe instructions');
        return false;
    }
    
    if (ingredients.length === 0) {
        alert('Please add at least one ingredient');
        return false;
    }
    
    return true;
}

// Dynamic Ingredient Row Addition
function addIngredientRow() {
    const container = document.getElementById('ingredients-container');
    const newRow = document.createElement('div');
    newRow.className = 'ingredient-row';
    newRow.innerHTML = `
        <input type="text" class="ingredient-name" placeholder="Ingredient">
        <input type="number" class="ingredient-amount" placeholder="Amount">
        <select class="ingredient-unit">
            <option value="g">grams</option>
            <option value="ml">milliliters</option>
            <option value="tsp">teaspoons</option>
            <option value="tbsp">tablespoons</option>
            <option value="cup">cups</option>
        </select>
        <button type="button" onclick="removeIngredientRow(this)">Remove</button>
    `;
    container.appendChild(newRow);
}

function removeIngredientRow(button) {
    button.parentElement.remove();
}

// Initialize all components
document.addEventListener('DOMContentLoaded', function() {
    initializeRichTextEditor();
    
    // Initialize star ratings
    document.querySelectorAll('.rating-container').forEach(container => {
        new StarRating(container);
    });
    
    // Initialize image upload previews
    const imageInput = document.getElementById('recipe-image');
    if (imageInput) {
        imageInput.addEventListener('change', function() {
            previewImage(this);
        });
    }
    
    // Initialize recipe scaling
    const scaleButtons = document.querySelectorAll('.scale-button');
    scaleButtons.forEach(button => {
        button.addEventListener('click', function() {
            scaleRecipe(parseFloat(this.dataset.factor));
        });
    });
});