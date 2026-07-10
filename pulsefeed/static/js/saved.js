document.addEventListener('DOMContentLoaded', () => {
    const savedNewsContainer = document.getElementById('saved-news-container');
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    
    async function fetchSavedArticles() {
        if (!savedNewsContainer) return;
        
        // Show loading state
        savedNewsContainer.innerHTML = `
            <div class="loading-container">
                <div class="spinner"></div>
                <p>Loading your saved articles...</p>
            </div>
        `;

        try {
            const response = await fetch('/get_saved_articles');
            const articles = await response.json();

            if (articles.error) {
                savedNewsContainer.innerHTML = `
                    <div class="news-error">
                        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="16"></line>
                            <line x1="12" y1="16" x2="12" y2="16"></line>
                        </svg>
                        <p>${articles.error}</p>
                    </div>
                `;
                return;
            }
            
            if (articles.length === 0) {
                savedNewsContainer.innerHTML = `
                    <div class="no-saved-articles">
                        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path>
                        </svg>
                        <p>You don't have any saved articles yet.</p>
                        <a href="/" class="button-primary">Browse News</a>
                    </div>
                `;
                return;
            }
            
            // Render saved articles
            savedNewsContainer.innerHTML = '';
            articles.forEach(article => {
                const articleElement = createArticleElement(article);
                savedNewsContainer.appendChild(articleElement);
            });
        } catch (error) {
            console.error('Error fetching saved articles:', error);
            savedNewsContainer.innerHTML = `
                <div class="news-error">
                    <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="8" y1="12" x2="16" y2="12"></line>
                    </svg>
                    <p>Failed to load saved articles. Please try again later.</p>
                </div>
            `;
        }
    }
    
    function createArticleElement(article) {
        const articleElement = document.createElement('div');
        articleElement.className = 'news-article saved-article';
        articleElement.dataset.id = article.id;
        
        const imageUrl = article.image_url || '/static/images/default-news.jpg';
        
        articleElement.innerHTML = `
            <div class="article-image">
                <img src="${imageUrl}" alt="${article.title}" onerror="this.src='/static/images/default-news.jpg'">
            </div>
            <div class="article-content">
                <h3 class="article-title">${article.title}</h3>
                <p class="article-source">${article.source} · ${formatDate(article.published_at)}</p>
                <p class="article-description">${article.description}</p>
                <div class="article-actions">
                    <a href="${article.url}" target="_blank" class="button-secondary">Read Full Article</a>
                    <button class="button-danger remove-saved" data-id="${article.id}">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <path d="M3 6h18"></path>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"></path>
                            <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                        Remove
                    </button>
                </div>
            </div>
        `;
        
        return articleElement;
    }
    
    function formatDate(dateString) {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
    }
    
    // Event delegation for removing saved articles
    if (savedNewsContainer) {
        savedNewsContainer.addEventListener('click', async (event) => {
            const removeButton = event.target.closest('.remove-saved');
            if (!removeButton) return;
            
            const articleId = removeButton.dataset.id;
            const articleElement = document.querySelector(`.news-article[data-id="${articleId}"]`);
            
            try {
                // Optimistic UI update
                articleElement.classList.add('removing');
                
                const response = await fetch('/remove_saved_article', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ article_id: articleId }),
                });
                
                const result = await response.json();
                
                if (result.success) {
                    articleElement.remove();
                    // Check if there are no more articles
                    if (savedNewsContainer.children.length === 0) {
                        fetchSavedArticles(); // This will show the "no articles" message
                    }
                } else {
                    // Revert optimistic update
                    articleElement.classList.remove('removing');
                    showNotification('Failed to remove article', 'error');
                }
            } catch (error) {
                console.error('Error removing article:', error);
                articleElement.classList.remove('removing');
                showNotification('Network error. Please try again.', 'error');
            }
        });
    }
    
    function showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.innerHTML = `
            <p>${message}</p>
            <button class="close-notification">×</button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            notification.classList.add('hiding');
            setTimeout(() => notification.remove(), 300);
        }, 5000);
        
        // Close button functionality
        notification.querySelector('.close-notification').addEventListener('click', () => {
            notification.classList.add('hiding');
            setTimeout(() => notification.remove(), 300);
        });
    }
    
    // Initialize search functionality
    if (searchInput && searchButton) {
        searchButton.addEventListener('click', () => {
            const query = searchInput.value.trim();
            if (query) {
                window.location.href = `/?q=${encodeURIComponent(query)}`;
            }
        });
        
        searchInput.addEventListener('keypress', (event) => {
            if (event.key === 'Enter') {
                const query = searchInput.value.trim();
                if (query) {
                    window.location.href = `/?q=${encodeURIComponent(query)}`;
                }
            }
        });
    }
    
    // Initialize
    if (savedNewsContainer) {
        fetchSavedArticles();
    }
});