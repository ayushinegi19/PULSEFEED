document.addEventListener('DOMContentLoaded', () => {
    // DOM elements
    const newsContainer = document.getElementById('news-container');
    const savedNewsContainer = document.getElementById('saved-news-container');
    const searchInput = document.getElementById('search-input');
    const searchButton = document.getElementById('search-button');
    
    // Store all news articles to filter locally
    let allNewsArticles = [];
    let allNewsClusters = [];

    // Add date display to navbar
    function setupDateDisplay() {
        const navbar = document.querySelector('.navbar') || document.querySelector('nav');
        if (navbar) {
            // Create date element
            const dateElement = document.createElement('div');
            dateElement.className = 'navbar-date';
            
            // Get current date in the format "date month year"
            const today = new Date();
            const options = { day: 'numeric', month: 'long', year: 'numeric' };
            const dateText = today.toLocaleDateString('en-US', options);
            dateElement.textContent = dateText;
            
            // Insert after logo if found, otherwise at beginning
            const logoContainer = navbar.querySelector('.logo-container') || navbar.querySelector('.navbar-brand');
            if (logoContainer) {
                logoContainer.insertAdjacentElement('afterend', dateElement);
            } else {
                navbar.insertAdjacentElement('afterbegin', dateElement);
            }
        }
    }

    
    // Format date
    function formatDate(dateString) {
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('en-US', {
                month: 'short',
                day: 'numeric',
                year: 'numeric'
            });
        } catch {
            return 'Unknown Date';
        }
    }

    // Show error messages
    function showError(container, message, showPreferencesButton = true) {
        if (!container) return;
        
        let errorHtml = `
            <div class="news-error">
                <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"></circle>
                    <line x1="12" y1="8" x2="12" y2="12"></line>
                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                </svg>
                <p>${message}</p>`;
                
        if (showPreferencesButton) {
            errorHtml += `<button onclick="window.location.href='/set_preferences'" class="error-btn">Update Preferences</button>`;
        }
        
        errorHtml += `</div>`;
        container.innerHTML = errorHtml;
    }

    // Show loading state
    function showLoading(container) {
        if (!container) return;
        
        container.innerHTML = `
            <div class="loading-container">
                <div class="spinner"></div>
                <p>Loading your personalized news...</p>
            </div>
        `;
    }

    // Fetch news articles
    async function fetchNews() {
        if (!newsContainer) return;
        
        showLoading(newsContainer);

        try {
            const response = await fetch('/get_news');
            const news = await response.json();

            if (news.error) {
                showError(newsContainer, news.error);
                return;
            }

            if (!news || news.length === 0) {
                showError(newsContainer, 'No news articles found. Try adjusting your preferences.');
                return;
            }

            // Store all news articles
            allNewsClusters = news;
            allNewsArticles = news.map(item => {
                if (item.representative) {
                    return item.representative;
                }
                return item;
            });
            
            // Render news articles
            renderNewsArticles(news);
        } catch (error) {
            showError(newsContainer, 'Unable to fetch news. Please check your connection.');
            console.error('Error fetching news:', error);
        }
    }

    // Render reliability badge HTML
    function renderReliabilityBadge(reliability) {
        if (!reliability) return '';
        return `<span class="reliability-badge" style="background-color: ${reliability.color};" title="Source: ${reliability.domain || 'unknown'}">${reliability.label}</span>`;
    }

    // Render news articles (supports both flat articles and clustered results)
    function renderNewsArticles(articles) {
        if (!newsContainer) return;
        
        newsContainer.innerHTML = articles.map(item => {
            let article, alsoCovered = '', clusterSize = 1;
            if (item.representative) {
                article = item.representative;
                clusterSize = item.cluster_size || 1;
                if (item.also_covered_by && item.also_covered_by.length > 0) {
                    alsoCovered = `<div class="also-covered">Also covered by: ${item.also_covered_by.join(', ')}</div>`;
                }
            } else {
                article = item;
            }
            const reliabilityBadge = renderReliabilityBadge(article.reliability);
            return `
            <div class="news-card">
                <img src="${article.urlToImage || '/static/placeholder.jpg'}" 
                     alt="${article.title}" 
                     onerror="this.src='/static/placeholder.jpg';">
                <div class="news-card-content">
                    <h3 class="news-card-title">${article.title}</h3>
                    <p class="news-card-description">${article.description || 'No description available'}</p>
                    ${alsoCovered}
                    <div class="news-meta">
                        <div class="news-source-date">
                            <span class="news-source">${article.source}</span>
                            ${reliabilityBadge}
                            <span class="news-date">${formatDate(article.publishedAt)}</span>
                        </div>
                        <div class="news-actions">
                            <a href="${article.url}" target="_blank" class="read-more">Read More</a>
                            <button class="save-btn" data-article='${JSON.stringify(article).replace(/'/g, "&apos;")}'>
                                <i class="bi bi-bookmark-plus"></i> Save
                            </button>
                        </div>
                    </div>
                </div>
            </div>`;
        }).join('');

        // Add event listeners to save buttons
        document.querySelectorAll('.save-btn').forEach(button => {
            button.addEventListener('click', function() {
                const articleData = JSON.parse(this.getAttribute('data-article').replace(/&apos;/g, "'"));
                saveArticle(articleData);
            });
        });

        // Log 'clicked' interactions when Read More links are opened
        document.querySelectorAll('.read-more').forEach(link => {
            link.addEventListener('click', function() {
                const card = this.closest('.news-card');
                const btn = card ? card.querySelector('.save-btn') : null;
                if (btn) {
                    const articleData = JSON.parse(btn.getAttribute('data-article').replace(/&apos;/g, "'"));
                    logInteraction(articleData, 'clicked');
                }
            });
        });
    }
    
    // Save article
    async function saveArticle(article) {
        try {
            const response = await fetch('/save_article', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(article)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                logInteraction(article, 'saved');
                // Create a temporary notification
                const notification = document.createElement('div');
                notification.className = 'save-notification';
                notification.innerHTML = `
                    <div class="notification-content">
                        <i class="bi bi-check-circle"></i>
                        <span>Article saved successfully!</span>
                    </div>
                `;
                document.body.appendChild(notification);
                
                // Remove notification after 3 seconds
                setTimeout(() => {
                    notification.style.opacity = '0';
                    setTimeout(() => notification.remove(), 300);
                }, 3000);
                
                return true;
            } else {
                console.error('Error saving article:', result.message);
                alert(result.message);
                return false;
            }
        } catch (error) {
            console.error('Error saving article:', error);
            alert('Failed to save article. Please try again.');
            return false;
        }
    }
    
    // Fetch saved articles
    async function fetchSavedArticles() {
        if (!savedNewsContainer) return;
        
        showLoading(savedNewsContainer);

        try {
            const response = await fetch('/get_saved_articles');
            const articles = await response.json();

            if (articles.error) {
                showError(savedNewsContainer, articles.error, false);
                return;
            }

            if (!articles || articles.length === 0) {
                savedNewsContainer.innerHTML = `
                    <div class="news-error">
                        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                        <p>You haven't saved any articles yet.</p>
                        <a href="/" class="error-btn">Browse News</a>
                    </div>
                `;
                return;
            }

            renderSavedArticles(articles);
        } catch (error) {
            showError(savedNewsContainer, 'Unable to fetch saved articles. Please try again later.', false);
            console.error('Error fetching saved articles:', error);
        }
    }
    
    // Render saved articles
    function renderSavedArticles(articles) {
        if (!savedNewsContainer) return;
        
        savedNewsContainer.innerHTML = articles.map(article => `
            <div class="news-card" data-id="${article.id}">
                <img src="${article.urlToImage || '/static/placeholder.jpg'}" 
                     alt="${article.title}" 
                     onerror="this.src='/static/placeholder.jpg';">
                <div class="news-card-content">
                    <h3 class="news-card-title">${article.title}</h3>
                    <p class="news-card-description">${article.description || 'No description available'}</p>
                    <div class="news-meta">
                        <div class="news-source-date">
                            <span class="news-source">${article.source}</span>
                            <span class="news-date">${formatDate(article.publishedAt)}</span>
                        </div>
                        <div class="news-actions">
                            <a href="${article.url}" target="_blank" class="read-more">Read More</a>
                            <button class="remove-saved-btn" data-id="${article.id}">
                                <i class="bi bi-trash"></i> Remove
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        // Add event listeners to remove buttons
        document.querySelectorAll('.remove-saved-btn').forEach(button => {
            button.addEventListener('click', async function() {
                const articleId = this.getAttribute('data-id');
                await removeFromSaved(articleId);
            });
        });
    }

    // Remove saved article
    async function removeFromSaved(articleId) {
        try {
            const response = await fetch(`/delete_saved_article/${articleId}`, {
                method: 'DELETE'
            });
            
            const result = await response.json();
            
            if (response.ok) {
                // Refresh saved articles
                fetchSavedArticles();
                return true;
            } else {
                console.error('Error removing article:', result.message);
                alert(result.message);
                return false;
            }
        } catch (error) {
            console.error('Error removing article:', error);
            alert('Failed to remove article. Please try again.');
            return false;
        }
    }
    
    // Search functionality
    function performSearch() {
        if (!searchInput) return;
        
        const searchTerm = searchInput.value.trim().toLowerCase();
        
        if (searchTerm === '') {
            // If search is empty, show all articles
            if (newsContainer) {
                renderNewsArticles(allNewsClusters);
            } else if (savedNewsContainer) {
                fetchSavedArticles();
            }
            return;
        }
        
        // Filter articles based on search term
        if (newsContainer && allNewsClusters.length > 0) {
            const filteredClusters = allNewsClusters.filter(item => {
                const article = item.representative || item;
                const title = article.title ? article.title.toLowerCase() : '';
                const description = article.description ? article.description.toLowerCase() : '';
                const source = article.source ? article.source.toLowerCase() : '';
                
                return title.includes(searchTerm) || 
                       description.includes(searchTerm) || 
                       source.includes(searchTerm);
            });
            
            if (filteredClusters.length === 0) {
                newsContainer.innerHTML = `
                    <div class="news-error">
                        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                        <p>No articles found matching "${searchTerm}"</p>
                        <button id="clear-search" class="error-btn">Clear Search</button>
                    </div>
                `;
                
                document.getElementById('clear-search').addEventListener('click', () => {
                    searchInput.value = '';
                    renderNewsArticles(allNewsClusters);
                });
            } else {
                renderNewsArticles(filteredClusters);
            }
        } else if (savedNewsContainer) {
            // For saved articles page, we'll search on the server
            searchSavedArticles(searchTerm);
        }
    }

    // Search saved articles
    async function searchSavedArticles(searchTerm) {
        try {
            const response = await fetch(`/search_saved_articles?query=${encodeURIComponent(searchTerm)}`);
            const articles = await response.json();
            
            if (articles.error) {
                showError(savedNewsContainer, articles.error, false);
                return;
            }
            
            if (!articles || articles.length === 0) {
                savedNewsContainer.innerHTML = `
                    <div class="news-error">
                        <svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                            <circle cx="12" cy="12" r="10"></circle>
                            <line x1="12" y1="8" x2="12" y2="12"></line>
                            <line x1="12" y1="16" x2="12.01" y2="16"></line>
                        </svg>
                        <p>No saved articles found matching "${searchTerm}"</p>
                        <button id="clear-saved-search" class="error-btn">Clear Search</button>
                    </div>
                `;
                
                document.getElementById('clear-saved-search').addEventListener('click', () => {
                    searchInput.value = '';
                    fetchSavedArticles();
                });
                return;
            }
            
            renderSavedArticles(articles);
            
        } catch (error) {
            console.error('Error searching saved articles:', error);
            showError(savedNewsContainer, 'Error searching saved articles. Please try again.', false);
        }
    }
    
    // Setup event listeners
    function setupEventListeners() {
        // Add event listeners for search
        if (searchButton) {
            searchButton.addEventListener('click', performSearch);
        }
        
        if (searchInput) {
            searchInput.addEventListener('keyup', (e) => {
                if (e.key === 'Enter') {
                    performSearch();
                }
            });
        }
    }

    // Initialize
    function init() {
        setupDateDisplay();
        setupEventListeners();
        
        // Initialize based on page
        if (newsContainer) {
            // On main news page
            fetchNews();
        } else if (savedNewsContainer) {
            // On saved articles page
            fetchSavedArticles();
        }
    }

    // Start the app
    init();

    // Log interaction (fire-and-forget, don't block UI)
    function logInteraction(article, interactionType) {
        try {
            fetch('/log_interaction', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ...article, interaction_type: interactionType })
            }).catch(err => console.error('Failed to log interaction:', err));
        } catch (err) {
            console.error('Failed to log interaction:', err);
        }
    }

    // Expose functions for global use
    window.fetchNews = fetchNews;
    window.fetchSavedArticles = fetchSavedArticles;
    window.saveArticle = saveArticle;
    window.removeFromSaved = removeFromSaved;
    window.logInteraction = logInteraction;
});