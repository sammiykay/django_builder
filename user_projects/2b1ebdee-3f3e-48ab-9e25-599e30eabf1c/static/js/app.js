class TagsInput {
    constructor(input, options) {
        this.input = input;
        this.options = options;
        this.tags = [];
        this.setupUI();
        this.bindEvents();
    }

    setupUI() {
        this.container = document.createElement('div');
        this.container.className = 'tags-input-container';
        this.input.parentNode.insertBefore(this.container, this.input);
        this.container.appendChild(this.input);
    }

    bindEvents() {
        this.input.addEventListener('keydown', (e) => {
            if (e.key === this.options.delimiter) {
                e.preventDefault();
                const tag = this.input.value.trim();
                if (tag) {
                    this.addTag(tag);
                    this.input.value = '';
                }
            }
        });
    }

    addTag(text) {
        if (!this.tags.includes(text)) {
            this.tags.push(text);
            const tag = document.createElement('span');
            tag.className = 'tag';
            tag.textContent = text;
            const removeButton = document.createElement('button');
            removeButton.textContent = '×';
            removeButton.addEventListener('click', () => this.removeTag(text, tag));
            tag.appendChild(removeButton);
            this.container.insertBefore(tag, this.input);
        }
    }

    removeTag(text, element) {
        this.tags = this.tags.filter(tag => tag !== text);
        element.remove();
    }
}