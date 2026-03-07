/**
 * Helper function to find a verse element within the currently active translation.
 * Uses a cache to avoid repeated DOM queries.
 * @param {string} verseIdentifier - The verse to find (e.g., "1:5a" or "1:5").
 * @returns {HTMLElement|null} The found element or null.
 */
function findElement(verseIdentifier) {
    if (!window.verseCache) return null;

    // 1. Direct lookup (covers exact part or exact whole verse)
    let element = window.verseCache.get(verseIdentifier);
    if (element) return element;

    // 2. Fallback: If looking for a verse part (e.g., "1:1b") and it's not found,
    //    try to find the whole verse element (e.g., "1:1").
    const partMatch = verseIdentifier.match(/^(\d+:\d+)[a-z]$/); // Matches "1:1b", "1:1c", etc.
    if (partMatch) {
        const wholeVerseIdentifier = partMatch[1]; // "1:1"
        element = window.verseCache.get(wholeVerseIdentifier);
        if (element) return element;
    }

    // 3. Fallback: If looking for a whole verse (e.g. "1:1") and it's not found,
    //    maybe it's split into parts in the HTML? Try to find the first part (e.g. "1:1a").
    element = window.verseCache.get(verseIdentifier + 'a');
    if (element) return element;

    return null; // No match found
}

/**
 * Builds a cache of verse elements for the active translation.
 * Should be called whenever the active translation changes.
 */
function buildVerseCache() {
    window.verseCache = new Map();
    const activeTranslation = document.querySelector('.translation-text.active');
    if (!activeTranslation) return;

    // Index parts
    const parts = activeTranslation.querySelectorAll('[data-verse-part]');
    parts.forEach(el => {
        window.verseCache.set(el.dataset.versePart, el);
    });

    // Index whole verses
    const wholes = activeTranslation.querySelectorAll('[data-verse]');
    wholes.forEach(el => {
        window.verseCache.set(el.dataset.verse, el);
    });
    // console.log(`[Performance] Verse cache built with ${window.verseCache.size} items.`);
}

/**
 * Debounce utility function.
 * @param {Function} func - The function to debounce.
 * @param {number} wait - The delay in milliseconds.
 * @returns {Function} The debounced function.
 */
function debounce(func, wait) {
    let timeout;
    return function (...args) {
        const context = this;
        clearTimeout(timeout);
        timeout = setTimeout(() => func.apply(context, args), wait);
    };
}

/**
 * Gets the current date in YYYY-MM-DD format based on the user's browser.
 * @returns {string} The formatted date string.
 */
function getCurrentDateString() {
    const today = new Date();
    // Use the browser's current date directly
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Formats a date object into "Fri. Oct 24, 2025" format.
 * @param {Date} date - The date object to format.
 * @returns {string} The formatted date string.
 */
function formatDisplayDate(date) {
    const options = { weekday: 'short', year: 'numeric', month: 'short', day: 'numeric' };
    // Adjust formatting slightly (e.g., add period after short weekday)
    let formatted = date.toLocaleDateString('en-US', options);
    // Insert period after weekday abbreviation if needed (e.g., "Fri" -> "Fri.")
    formatted = formatted.replace(/^(\w{3}),/, '$1.');
    return formatted;
}

// --- Book Slug Mapping (Simplified for JS) ---
const BOOK_SLUG_MAP_JS = {
    "genesis": "genesis", "exodus": "exodus", "leviticus": "leviticus", "numbers": "numbers", "deuteronomy": "deuteronomy",
    "joshua": "joshua", "judges": "judges", "ruth": "ruth", "1 samuel": "1-samuel", "2 samuel": "2-samuel",
    "1 kings": "1-kings", "2 kings": "2-kings", "1 chronicles": "1-chronicles", "2 chronicles": "2-chronicles",
    "ezra": "ezra", "nehemiah": "nehemiah", "tobit": "tobit", "judith": "judith", "esther": "esther",
    "1 maccabees": "1-maccabees", "2 maccabees": "2-maccabees", "job": "job", "psalm": "psalms", "proverbs": "proverbs",
    "ecclesiastes": "ecclesiastes", "song of songs": "song-of-songs", "wisdom": "wisdom", "sirach": "sirach",
    "isaiah": "isaiah", "jeremiah": "jeremiah", "lamentations": "lamentations", "baruch": "baruch", "ezekiel": "ezekiel",
    "daniel": "daniel", "hosea": "hosea", "joel": "joel", "amos": "amos", "obadiah": "obadiah",
    "jonah": "jonah", "micah": "micah", "nahum": "nahum", "habakkuk": "habakkuk", "zephaniah": "zephaniah",
    "haggai": "haggai", "zechariah": "zechariah", "malachi": "malachi", "matthew": "matthew", "mark": "mark",
    "luke": "luke", "john": "john", "acts": "acts", "romans": "romans", "1 corinthians": "1-corinthians",
    "2 corinthians": "2-corinthians", "galatians": "galatians", "ephesians": "ephesians", "philippians": "philippians",
    "colossians": "colossians", "1 thessalonians": "1-thessalonians", "2 thessalonians": "2-thessalonians",
    "1 timothy": "1-timothy", "2 timothy": "2-timothy", "titus": "titus", "philemon": "philemon",
    "hebrews": "hebrews", "james": "james", "1 peter": "1-peter", "2 peter": "2-peter",
    "1 john": "1-john", "2 john": "2-john", "3 john": "3-john", "jude": "jude", "revelation": "revelation",
    // Common Abbreviations
    "ps": "psalms", "1 cor": "1-corinthians", "2 cor": "2-corinthians", "gal": "galatians", "eph": "ephesians",
    "phil": "philippians", "col": "colossians", "1 thes": "1-thessalonians", "2 thes": "2-thessalonians",
    "1 tm": "1-timothy", "2 tm": "2-timothy", "ti": "titus", "phlm": "philemon", "heb": "hebrews",
    "jas": "james", "1 pt": "1-peter", "2 pt": "2-peter", "1 jn": "1-john", "2 jn": "2-john", "3 jn": "3-john",
    "jud": "jude", "rv": "revelation"
};
const SORTED_BOOK_KEYS_JS = Object.keys(BOOK_SLUG_MAP_JS).sort((a, b) => b.length - a.length); // Sort descending by length

/**
 * --- Parses a full scripture reference string into book slug and ranges ---
 * @param {string} refString - The scripture reference string.
 * @returns {object|null} An object { bookSlug: string, ranges: array } or null if parsing fails.
 */
function parseFullReference(refString) {
    if (!refString) return null;
    const normalizedRef = refString.replace(/NABRE/i, '').replace(/[—–]/g, '-').trim(); // Normalize dashes

    let bookSlug = null;
    let restOfString = null;

    for (const key of SORTED_BOOK_KEYS_JS) {
        const pattern = new RegExp(`\\b${key}\\b`, 'i');
        const match = normalizedRef.match(pattern);
        if (match) {
            const potentialRest = normalizedRef.substring(match.index + match[0].length).trim();
            if (/^\d/.test(potentialRest)) {
                bookSlug = BOOK_SLUG_MAP_JS[key.toLowerCase()];
                restOfString = potentialRest;
                break;
            }
        }
    }

    if (!bookSlug || restOfString === null) {
        console.warn(`[parseFullReference] Could not find book in: "${refString}"`);
        return null;
    }

    const ranges = [];
    let lastChapter = null;
    const parts = restOfString.split(/[,;]/);

    for (const part of parts) {
        const trimmedPart = part.trim();
        if (!trimmedPart) continue;

        let startChapter, startVerseStr, endChapter, endVerseStr;

        try {
            const crossChapterMatch = trimmedPart.match(/^(\d+):(\d+[a-z]?)\s*-\s*(\d+):(\d+[a-z]?)$/);
            if (crossChapterMatch) {
                startChapter = parseInt(crossChapterMatch[1]);
                startVerseStr = crossChapterMatch[2];
                endChapter = parseInt(crossChapterMatch[3]);
                endVerseStr = crossChapterMatch[4];
                lastChapter = endChapter;
            } else {
                const withinChapterRangeMatch = trimmedPart.match(/^(?:(\d+):)?(\d+[a-z]?)\s*-\s*(\d+[a-z]?)$/);
                if (withinChapterRangeMatch) {
                    startChapter = withinChapterRangeMatch[1] ? parseInt(withinChapterRangeMatch[1]) : lastChapter;
                    startVerseStr = withinChapterRangeMatch[2];
                    endChapter = startChapter;
                    endVerseStr = withinChapterRangeMatch[3];
                    lastChapter = startChapter;
                } else {
                    const singleVerseMatch = trimmedPart.match(/^(?:(\d+):)?(\d+[a-z]?)$/);
                    if (singleVerseMatch) {
                        startChapter = singleVerseMatch[1] ? parseInt(singleVerseMatch[1]) : lastChapter;
                        startVerseStr = singleVerseMatch[2];
                        endChapter = startChapter;
                        endVerseStr = startVerseStr; // Start and end are the same
                        lastChapter = startChapter;
                    } else {
                        console.warn(`[parseFullReference] Could not parse part: "${trimmedPart}" in "${refString}"`);
                        continue;
                    }
                }
            }

            if (startChapter && startVerseStr && endChapter && endVerseStr) {
                ranges.push({
                    startChapter: startChapter,
                    startVerse: parseInt(startVerseStr),
                    startPart: (startVerseStr.match(/[a-z]/) || [''])[0],
                    endChapter: endChapter,
                    endVerse: parseInt(endVerseStr),
                    endPart: (endVerseStr.match(/[a-z]/) || [''])[0]
                });
            }

        } catch (e) {
            console.warn(`[parseFullReference] Error parsing part "${trimmedPart}" in "${refString}":`, e);
        }
    }

    if (ranges.length === 0) return null;
    return { bookSlug, ranges };
}


/**
 * --- Checks if the current page chapter intersects with any of the day's readings ---
 * @param {string} currentBookSlug - The slug of the book for the current page.
 * @param {number} currentChapterNum - The chapter number for the current page.
 * @param {object} todaysReadings - The readings data object for the current day.
 * @returns {boolean} True if there is an intersection, false otherwise.
 */
function checkReadingIntersection(currentBookSlug, currentChapterNum, todaysReadings) {
    if (!todaysReadings || !currentBookSlug || isNaN(currentChapterNum)) {
        return false;
    }

    const readingKeys = ['reading_1', 'psalm', 'reading_2', 'allelulia', 'gospel'];

    for (const key of readingKeys) {
        const refString = todaysReadings[key];
        if (refString) {
            const parsedRef = parseFullReference(refString);
            if (parsedRef && parsedRef.bookSlug === currentBookSlug) {
                for (const range of parsedRef.ranges) {
                    if (currentChapterNum >= range.startChapter && currentChapterNum <= range.endChapter) {
                        return true; // Found an intersection
                    }
                }
            }
        }
    }
    return false; // No intersection found
}


/**
 * Creates and displays the daily readings popup.
 * @param {object} readingsData - The readings data object for the current day.
 */
function displayReadingsPopup(readingsData) {
    if (!readingsData) return;

    const body = document.body;
    const isIndexPage = window.location.pathname.endsWith('index.html') || window.location.pathname === '/' || window.location.pathname.endsWith('/');
    const isAboutPage = window.location.pathname.endsWith('about.html');
    const isChapterPage = window.location.pathname.includes('/bible/');
    const currentBookSlug = body.dataset.book;
    const currentChapterNum = parseInt(body.dataset.chapter, 10);

    // Use the date string directly from data, assume it's YYYY-MM-DD
    const dateValue = readingsData.date;
    // Create a date object for formatting
    const readingDate = new Date(dateValue + 'T00:00:00'); // Add time component to avoid timezone issues

    // --- Skip popup on index page (has its own inline readings pane) ---
    if (isIndexPage || body.classList.contains('landing-page')) return;

    // --- Only show on chapter pages if relevant ---
    if (isChapterPage) {
        const intersects = checkReadingIntersection(currentBookSlug, currentChapterNum, readingsData);
        if (!intersects) {
            console.log("Current chapter page does not intersect with today's readings. Hiding popup.");
            return;
        }
    }

    let popupContent = '';
    const readingSequence = [];

    const createLink = (text, link) => link ? `<a href="../${link}">${text}</a>` : text;

    const addReadingToSequence = (label, readingRef, readingLink) => {
        if (readingRef && readingLink) {
            readingSequence.push({ ref: readingRef, link: readingLink, label: label });
        }
    };

    // Populate the sequence first
    addReadingToSequence('Reading 1', readingsData.reading_1, readingsData.reading_1_link);
    addReadingToSequence('Psalm', readingsData.psalm, readingsData.psalm_link);
    addReadingToSequence('Reading 2', readingsData.reading_2, readingsData.reading_2_link);
    addReadingToSequence('Alleluia', readingsData.allelulia, readingsData.allelulia_link);
    addReadingToSequence('Gospel', readingsData.gospel, readingsData.gospel_link);

    // --- Build Popup Content ---
    popupContent += `<button class="popup-close-btn">&times;</button>`; // Moved to top for absolute positioning
    popupContent += `<div class="popup-header">`;
    popupContent += `<div>`;
    popupContent += `<h4 style="margin-bottom: 0;">${readingsData.name || 'Daily Readings'}</h4>`;
    popupContent += `<div class="popup-date-container" style="cursor: pointer;">`;
    popupContent += `<p class="popup-date-text">${formatDisplayDate(readingDate)}</p>`;
    popupContent += `<input type="date" class="popup-date-picker" value="${dateValue}">`;
    popupContent += `</div>`;
    popupContent += `</div>`;
    popupContent += `</div>`;

    popupContent += `<ul class="popup-reading-list">`;
    if (readingSequence.length > 0) {
        readingSequence.forEach(reading => {
            popupContent += `<li><strong>${reading.label}:</strong> ${createLink(reading.ref, reading.link)}</li>`;
        });
    } else {
        popupContent += `<li>No readings available for this date.</li>`;
    }
    popupContent += `</ul>`;

    // --- Create and Inject Popup ---
    const popupDiv = document.createElement('div');
    popupDiv.id = 'daily-readings-popup';
    popupDiv.innerHTML = popupContent;

    const liturgicalColor = (readingsData.color || '').toLowerCase();
    if (liturgicalColor) {
        popupDiv.classList.add(`liturgical-color-${liturgicalColor}`);
    } else {
        popupDiv.classList.add(`liturgical-color-default`);
    }

    body.appendChild(popupDiv);

    // close functionality
    const closeButton = popupDiv.querySelector('.popup-close-btn');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            popupDiv.style.display = 'none';
        });
    }

    // --- Event listener for date picker ---
    const datePicker = popupDiv.querySelector('.popup-date-picker');
    const dateContainer = popupDiv.querySelector('.popup-date-container');

    if (dateContainer && datePicker) {
        dateContainer.addEventListener('click', () => {
            if ('showPicker' in HTMLInputElement.prototype) {
                try {
                    datePicker.showPicker();
                } catch (error) {
                    console.warn('showPicker failed:', error);
                    // Fallback: try clicking it directly (might not work if hidden)
                    datePicker.click();
                }
            } else {
                // Fallback for older browsers
                datePicker.click();
            }
        });
    }

    if (datePicker) {
        datePicker.addEventListener('change', (event) => {
            const newDateStr = event.target.value;
            const newReadings = window.allUsccbReadings.find(reading => reading.date === newDateStr);

            popupDiv.remove(); // Remove current popup

            if (newReadings) {
                // Update global-scoped variable that highlights depend on
                window.todaysReadingsData = newReadings;
                displayReadingsPopup(newReadings); // Show popup for the new date
            } else {
                window.todaysReadingsData = null; // Clear data
                displayReadingsPopup({ // Show a "not found" popup
                    date: newDateStr,
                    name: "No readings found for this date",
                    color: "black"
                });
            }
            // Manually call redraw to update highlights for the new date
            highlightDailyReadings(window.todaysReadingsData);
        });
    }
}

/**
 * --- Highlights verses by drawing a continuous block ---
 * @param {object} todaysReadings - The readings data object for the current day.
 */
/**
 * --- Highlights verses by drawing a continuous block ---
 * @param {object} todaysReadings - The readings data object for the current day.
 */
function highlightDailyReadings(todaysReadings) {
    const bibleTextContainer = document.querySelector('.bible-text');
    const body = document.body;
    const currentBookSlug = body.dataset.book;
    const currentChapterNum = parseInt(body.dataset.chapter, 10);

    if (!todaysReadings || !currentBookSlug || isNaN(currentChapterNum) || !bibleTextContainer) {
        return; // Not a chapter page or no data
    }

    // 1. Build a list of applicable ranges for this specific page
    const applicableRanges = [];
    const readingKeys = ['reading_1', 'psalm', 'reading_2', 'allelulia', 'gospel'];

    for (const key of readingKeys) {
        const refString = todaysReadings[key];
        if (refString) {
            const parsedRef = parseFullReference(refString);
            if (parsedRef && parsedRef.bookSlug === currentBookSlug) {
                for (const range of parsedRef.ranges) {
                    if (currentChapterNum >= range.startChapter && currentChapterNum <= range.endChapter) {
                        applicableRanges.push(range);
                    }
                }
            }
        }
    }

    if (applicableRanges.length === 0) {
        // Clear highlights if no readings apply
        document.querySelectorAll('.daily-reading-highlight-block').forEach(el => el.remove());
        return;
    }

    // 2. Find all verse elements on the page (for calculations)
    const allVersesOnPage = document.querySelectorAll(`.translation-text.active p[data-verse^="${currentChapterNum}:"], .translation-text.active span[data-verse-part^="${currentChapterNum}:"]`);
    if (allVersesOnPage.length === 0) return;

    const firstVerseOnPage = allVersesOnPage[0].dataset.verse || allVersesOnPage[0].dataset.versePart;
    const lastVerseOnPage = allVersesOnPage[allVersesOnPage.length - 1].dataset.verse || allVersesOnPage[allVersesOnPage.length - 1].dataset.versePart;

    // 3. Measure Phase: Calculate positions
    const highlightsToDraw = [];
    applicableRanges.forEach(range => {
        const { startChapter, startVerse, startPart, endChapter, endVerse, endPart } = range;

        // Determine the start and end element IDs for this specific page
        let startID, endID;

        if (startChapter < currentChapterNum) {
            startID = firstVerseOnPage; // Reading starts before this chapter
        } else {
            startID = `${startChapter}:${startVerse}${startPart}`;
        }

        if (endChapter > currentChapterNum) {
            endID = lastVerseOnPage; // Reading ends after this chapter
        } else {
            endID = `${endChapter}:${endVerse}${endPart}`;
        }

        const startEl = findElement(startID);
        const endEl = findElement(endID);

        if (startEl && endEl) {
            const containerRect = bibleTextContainer.getBoundingClientRect();
            const startRect = startEl.getBoundingClientRect();
            const endRect = endEl.getBoundingClientRect();

            const padding = 4; // 4px padding
            // Measure positions relative to the bibleTextContainer
            const startPos = startRect.top - containerRect.top - padding;
            const endPos = endRect.bottom - containerRect.top + padding;
            const height = endPos - startPos;
            highlightsToDraw.push({ top: startPos, height: height });
        }
    });

    // 4. Mutate Phase: Clear and Draw
    document.querySelectorAll('.daily-reading-highlight-block').forEach(el => el.remove());

    const fragment = document.createDocumentFragment();
    highlightsToDraw.forEach(h => {
        const highlightBlock = document.createElement('div');
        highlightBlock.className = 'daily-reading-highlight-block';
        highlightBlock.style.top = h.top + 'px';
        highlightBlock.style.height = h.height + 'px';
        fragment.appendChild(highlightBlock);
    });

    bibleTextContainer.appendChild(fragment);
}



/**
 * --- Initializes the Search Modal ---
 */
function initSearchModal() {
    // 1. Create Modal HTML
    const modalOverlay = document.createElement('div');
    modalOverlay.id = 'search-modal-overlay';
    modalOverlay.innerHTML = `
        <div id="search-modal">
            <div class="search-input-container">
                <input type="text" id="search-input" placeholder="Go to... (e.g. 'Gen 1', 'John 3')">
                <span class="search-icon">↵</span>
            </div>
            <div id="search-results"></div>
            <div class="search-hint">
                <span>Type a book and chapter</span>
                <span><span class="shortcut-badge">Esc</span> to close</span>
            </div>
        </div>
    `;
    document.body.appendChild(modalOverlay);

    const searchInput = modalOverlay.querySelector('#search-input');
    const searchResults = modalOverlay.querySelector('#search-results');

    // 2. Toggle Logic
    const toggleModal = (show) => {
        if (show) {
            modalOverlay.classList.add('active');
            searchInput.value = '';
            searchResults.innerHTML = '';
            searchInput.focus();
        } else {
            modalOverlay.classList.remove('active');
            searchInput.blur();
        }
    };

    // 3. Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
        // Open: '/' or Cmd+K
        if ((e.key === '/' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) ||
            ((e.metaKey || e.ctrlKey) && e.key === 'k')) {
            e.preventDefault();
            toggleModal(true);
        }
        // Close: Esc
        if (e.key === 'Escape' && modalOverlay.classList.contains('active')) {
            toggleModal(false);
        }
    });

    // Close on click outside
    modalOverlay.addEventListener('click', (e) => {
        if (e.target === modalOverlay) {
            toggleModal(false);
        }
    });

    // 4. Search Logic
    const handleSearch = () => {
        const query = searchInput.value.trim();
        if (!query) {
            searchResults.innerHTML = '';
            return;
        }

        // Parse query: "Book Chapter"
        const match = query.match(/^([1-3]?\s*[a-zA-Z\s]+?)\s*(\d*)$/);

        if (!match) {
            searchResults.innerHTML = '<div class="search-result-item">No match found</div>';
            return;
        }

        const bookQuery = match[1].trim().toLowerCase();
        const chapterQuery = match[2] ? parseInt(match[2]) : 1;

        // Find matching books
        const matches = [];
        for (const key of SORTED_BOOK_KEYS_JS) {
            if (key.includes(bookQuery)) {
                matches.push({
                    name: key.split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' '),
                    slug: BOOK_SLUG_MAP_JS[key],
                    chapter: chapterQuery
                });
            }
        }

        // Limit results
        const topMatches = matches.slice(0, 5);

        // Render results
        searchResults.innerHTML = '';
        topMatches.forEach((match, index) => {
            const div = document.createElement('div');
            div.className = `search-result-item ${index === 0 ? 'selected' : ''}`;
            div.innerHTML = `
                <span class="book-name">${match.name}</span>
                <span class="chapter-num">Chapter ${match.chapter}</span>
            `;
            div.addEventListener('click', () => {
                navigateToChapter(match.slug, match.chapter);
            });
            searchResults.appendChild(div);
        });

        if (topMatches.length === 0) {
            searchResults.innerHTML = '<div class="search-result-item">No book found</div>';
        }
    };

    // 5. Navigation Logic
    const navigateToChapter = (bookSlug, chapter) => {
        const filename = `${bookSlug}-${String(chapter).padStart(2, '0')}.html`;
        let targetUrl = '';

        if (window.location.pathname.includes('/bible/')) {
            targetUrl = filename;
        } else {
            targetUrl = `bible/${filename}`;
        }

        window.location.href = targetUrl;
    };

    // Input Event Listeners
    searchInput.addEventListener('input', handleSearch);

    searchInput.addEventListener('keydown', (e) => {
        const items = searchResults.querySelectorAll('.search-result-item');
        let selectedIndex = -1;

        items.forEach((item, index) => {
            if (item.classList.contains('selected')) {
                selectedIndex = index;
            }
        });

        if (e.key === 'ArrowDown') {
            e.preventDefault(); // Prevent cursor moving to end of input
            if (items.length > 0) {
                if (selectedIndex >= 0) {
                    items[selectedIndex].classList.remove('selected');
                }
                // Move down, or select first if none selected
                const nextIndex = selectedIndex < items.length - 1 ? selectedIndex + 1 : 0;
                items[nextIndex].classList.add('selected');
                items[nextIndex].scrollIntoView({ block: 'nearest' });
            }
        } else if (e.key === 'ArrowUp') {
            e.preventDefault(); // Prevent cursor moving to start of input
            if (items.length > 0) {
                if (selectedIndex >= 0) {
                    items[selectedIndex].classList.remove('selected');
                }
                // Move up, or select last if none selected (or loop back to bottom)
                const prevIndex = selectedIndex > 0 ? selectedIndex - 1 : items.length - 1;
                items[prevIndex].classList.add('selected');
                items[prevIndex].scrollIntoView({ block: 'nearest' });
            }
        } else if (e.key === 'Enter') {
            e.preventDefault();
            const selected = searchResults.querySelector('.selected');
            if (selected) {
                selected.click();
            } else if (items.length > 0) {
                // Fallback to first item if nothing selected (though handleSearch selects first by default)
                items[0].click();
            }
        }
    });
}


// --- Theme Management Logic ---
/**
 * Initializes the theme based on localStorage or system preference.
 */
function initTheme() {
    // Force light mode on index and about pages
    const isLightOnlyPage = window.location.pathname.endsWith('index.html') ||
        window.location.pathname.endsWith('about.html') ||
        window.location.pathname === '/' ||
        window.location.pathname === '/liturgybible.github.io/';

    if (isLightOnlyPage) {
        document.documentElement.setAttribute('data-theme', 'light');
        return;
    }

    const savedTheme = localStorage.getItem('theme');
    const systemPrefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const theme = savedTheme || (systemPrefersDark ? 'dark' : 'light');

    document.documentElement.setAttribute('data-theme', theme);
    updateThemeToggleUI(theme);
}

/**
 * Toggles the theme between light and dark.
 */
function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

    document.documentElement.setAttribute('data-theme', newTheme);
    localStorage.setItem('theme', newTheme);
    updateThemeToggleUI(newTheme);
}

/**
 * Updates the theme toggle button icon/label.
 * @param {string} theme - The current theme ('light' or 'dark').
 */
/**
 * Updates the theme toggle button icon/label.
 * @param {string} theme - The current theme ('light' or 'dark').
 */
function updateThemeToggleUI(theme) {
    const toggleBtn = document.getElementById('theme-toggle');
    if (toggleBtn) {
        const sunIcon = `<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
        const moonIcon = `<svg viewBox="0 0 24 24" width="20" height="20" stroke="currentColor" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;

        toggleBtn.innerHTML = theme === 'dark' ? sunIcon : moonIcon;
        toggleBtn.title = theme === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode';
        // Use white for sun in dark mode, and dark grey for moon in light mode
        toggleBtn.style.color = theme === 'dark' ? '#FFFFFF' : '#777777';
    }
}

/**
 * Adds the theme toggle button to the header controls.
 */
function addThemeToggle() {
    // Only add toggle on pages that support dark mode
    const isLightOnlyPage = window.location.pathname.endsWith('index.html') ||
        window.location.pathname.endsWith('about.html') ||
        window.location.pathname === '/' ||
        window.location.pathname === '/liturgybible.github.io/';

    if (isLightOnlyPage) return;

    const headerControls = document.querySelector('.header-controls');
    if (headerControls && !document.getElementById('theme-toggle')) {
        const toggleBtn = document.createElement('button');
        toggleBtn.id = 'theme-toggle';
        toggleBtn.className = 'theme-toggle-btn';
        toggleBtn.style.background = 'none';
        toggleBtn.style.border = 'none';
        toggleBtn.style.fontSize = '1.2rem';
        toggleBtn.style.cursor = 'pointer';
        toggleBtn.style.padding = '0.5rem';
        toggleBtn.style.display = 'flex';
        toggleBtn.style.alignItems = 'center';
        toggleBtn.style.justifyContent = 'center';
        toggleBtn.addEventListener('click', toggleTheme);

        // Insert before translation switcher if it exists
        const switcher = document.getElementById('translation-switcher');
        if (switcher) {
            headerControls.insertBefore(toggleBtn, switcher);
        } else {
            headerControls.appendChild(toggleBtn);
        }

        const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
        updateThemeToggleUI(currentTheme);
    }
}

// Call initTheme immediately to prevent flash
initTheme();


// --- MAIN SCRIPT EXECUTION ON LOAD ---
window.addEventListener('load', () => {
    initSearchModal();
    addThemeToggle();

    const body = document.body;
    const book = body.dataset.book;
    const chapter = body.dataset.chapter;

    // --- Make readings data globally accessible ---
    window.todaysReadingsData = null; // Store today's readings to pass to other functions
    window.allUsccbReadings = []; // Store all readings

    // --- Reference Data (CCC & RM) ---
    window.bookCccRefs = null; // Store per-book CCC refs
    window.cccTextData = null; // Lazy-loaded full CCC text
    window.cccTextPromise = null; // Promise to manage lazy-loading
    window.bookRmRefs = null; // Store all RM refs (from single file)
    window.rmTextData = null; // Lazy-loaded full RM text
    window.rmTextPromise = null; // Promise to manage lazy-loading

    // --- Daily Readings Popup Logic ---
    const todayStr = getCurrentDateString();
    fetch('../data_usccb/usccb-readings.json')
        .then(response => {
            if (!response.ok) throw new Error('Failed to load readings data');
            return response.json();
        })
        .then(data => {
            window.allUsccbReadings = data; // Store globally
            window.todaysReadingsData = window.allUsccbReadings.find(reading => reading.date === todayStr);

            if (window.todaysReadingsData) {
                displayReadingsPopup(window.todaysReadingsData);
                // Also highlight readings on load
                if (book && chapter) {
                    highlightDailyReadings(window.todaysReadingsData);
                }
            } else {
                console.log("No readings found for today:", todayStr);
            }
        })
        .catch(error => {
            console.error("Error fetching or processing daily readings:", error);
        });
    // --- End Daily Readings Popup Logic ---

    // --- CCC Reference Logic ---
    if (book && chapter) {
        fetch(`../data/ccc-refs/${book}.json`)
            .then(response => {
                if (!response.ok) throw new Error(`Could not load CCC refs for ${book}.`);
                return response.json();
            })
            .then(data => {
                window.bookCccRefs = data;
                // Inject pills *after* translation is applied
                redraw();
            })
            .catch(error => console.error("Error fetching CCC references:", error));
    }
    // --- End CCC Reference Logic ---

    // --- Roman Missal Reference Logic ---
    if (book && chapter) {
        fetch(`../data/roman-missal-refs/roman-missal-refs.json`)
            .then(response => {
                if (!response.ok) throw new Error(`Could not load RM refs.`);
                return response.json();
            })
            .then(data => {
                // The file contains all books, so we extract the one we need
                window.bookRmRefs = data[book] || null;
                redraw();
            })
            .catch(error => console.error("Error fetching Roman Missal references:", error));
    }
    // --- End Roman Missal Reference Logic ---


    // --- Mobile Warning Banner ---
    const topNav = document.querySelector('.top-nav');
    if (topNav) {
        const warningBanner = document.createElement('div');
        warningBanner.id = 'mobile-warning-banner';
        warningBanner.innerHTML = 'View on wider screen to see liturgical annotations.';
        topNav.insertAdjacentElement('afterend', warningBanner);
    }

    if (!book || !chapter) {
        console.log("Not a chapter page, skipping annotation logic.");
        return;
    }

    let lectionaryReadingsData = [];
    let divineOfficeData = [];

    const redraw = () => {
        // --- References: Clear and re-inject pills FIRST ---
        // This ensures they affect the layout (height) before we measure for annotations
        clearRefPills();
        if ((window.bookCccRefs || window.bookRmRefs) && chapter) {
            injectRefPills(window.bookCccRefs, window.bookRmRefs, parseInt(chapter, 10));
        }

        drawAnnotations(lectionaryReadingsData, divineOfficeData);
        // Also re-highlight readings when redrawing (e.g., on translation switch)
        highlightDailyReadings(window.todaysReadingsData);
    };

    // --- Translation Switcher Logic ---
    const switcher = document.getElementById('translation-switcher');

    // Define applyTranslation in a scope where it can be used by everyone
    const applyTranslation = () => {
        const selectedValue = switcher ? switcher.value : 'dra';
        document.querySelectorAll('.translation-text').forEach(div => {
            div.classList.remove('active');
        });

        let selectedTranslationDiv = document.querySelector(`.translation-text.${selectedValue}`);
        if (!selectedTranslationDiv) {
            selectedTranslationDiv = document.querySelector('.translation-text');
        }

        if (selectedTranslationDiv) {
            selectedTranslationDiv.classList.add('active');
        }

        if (switcher) {
            localStorage.setItem('selectedTranslation', selectedValue);
        }

        buildVerseCache(); // Rebuild cache for new translation
        redraw(); // Redraw everything
    };

    if (switcher) {
        const savedTranslation = localStorage.getItem('selectedTranslation');
        if (savedTranslation) {
            switcher.value = savedTranslation;
        }
        switcher.addEventListener('change', applyTranslation);
    }

    // Initialize translation and cache immediately on load
    applyTranslation();

    // --- ARROW KEY NAVIGATION ---
    document.addEventListener('keydown', function (event) {
        const prevLink = document.querySelector('.bottom-nav a:first-of-type');
        const nextLink = document.querySelector('.bottom-nav a:last-of-type');

        if (event.key === 'ArrowLeft') {
            if (prevLink && prevLink.hasAttribute('href')) {
                window.location.href = prevLink.href;
            }
        } else if (event.key === 'ArrowRight') {
            if (nextLink && nextLink.hasAttribute('href')) {
                window.location.href = nextLink.href;
            }
        }
    });

    const currentChapterNum = parseInt(chapter, 10);

    const parseVerse = (verseStr) => {
        const [c, v] = verseStr.split(/[:a-z]/).map(Number);
        return { chapter: c, verse: v };
    };

    const isReadingInChapter = (reading) => {
        const segments = reading.segments || [{ start: reading.start, end: reading.end }];
        if (!segments[0].start) return false;
        const startChapter = parseVerse(segments[0].start).chapter;
        const endChapter = parseVerse(segments[segments.length - 1].end).chapter;
        return currentChapterNum >= startChapter && currentChapterNum <= endChapter;
    };

    fetch(`../data/${book}.json`)
        .then(response => {
            if (!response.ok) throw new Error(`Could not load data for ${book}.`);
            return response.json();
        })
        .then(data => {
            lectionaryReadingsData = (data.lectionaryReadings || []).filter(isReadingInChapter);
            divineOfficeData = (data.divineOffice || []).filter(isReadingInChapter);

            // Data is loaded, redraw to show annotations
            redraw();

            window.addEventListener('resize', debounce(redraw, 200));
        })
        .catch(error => console.error("Error loading annotation data:", error));
});

function drawAnnotations(lectionaryReadings, divineOffice) {
    const leftMargin = document.querySelector('.annotations-margin-left');
    const rightMargin = document.querySelector('.annotations-margin-right');

    if (!leftMargin || !rightMargin) return;

    leftMargin.innerHTML = '';
    rightMargin.innerHTML = '';

    renderSide(lectionaryReadings, leftMargin, false);
    renderSide(divineOffice, rightMargin, true);
}

function renderSide(readings, container, isRightSided) {
    const bibleTextContainer = document.querySelector('.bible-text');
    if (!bibleTextContainer) return;

    const currentChapterNum = parseInt(document.body.dataset.chapter, 10);
    const parseVerse = (verseStr) => {
        const [c, v] = verseStr.split(/[:a-z]/).map(Number);
        return { chapter: c, verse: v };
    };

    let occupiedSlots = [];
    const positionalReadings = [];

    // --- Step 1: Calculate positions and slots for all readings (MEASURE PHASE) ---
    readings.forEach(reading => {
        const originalSegments = reading.segments || [{ start: reading.start, end: reading.end }];
        if (!originalSegments[0].start) return;

        const allVersesOnPage = document.querySelectorAll(`.translation-text.active p[data-verse^="${currentChapterNum}:"], .translation-text.active span[data-verse-part^="${currentChapterNum}:"]`);
        if (allVersesOnPage.length === 0) return;

        const firstVerseOnPage = allVersesOnPage[0].dataset.verse || allVersesOnPage[0].dataset.versePart;
        const lastVerseOnPage = allVersesOnPage[allVersesOnPage.length - 1].dataset.verse || allVersesOnPage[allVersesOnPage.length - 1].dataset.versePart;

        const segmentsToDraw = [];
        originalSegments.forEach(segment => {
            const segStart = parseVerse(segment.start);
            const segEnd = parseVerse(segment.end);
            if (currentChapterNum < segStart.chapter || currentChapterNum > segEnd.chapter) return;

            let drawStartVerse, drawEndVerse;

            // Determine Start
            if (segStart.chapter < currentChapterNum) {
                drawStartVerse = firstVerseOnPage;
            } else {
                drawStartVerse = segment.start;
            }

            // Determine End
            if (segEnd.chapter > currentChapterNum || segEnd.verse === 1000) {
                drawEndVerse = lastVerseOnPage; // Use the last verse found on the page
            } else {
                drawEndVerse = segment.end;
            }

            // MEASURE HERE
            const startVerseEl = findElement(drawStartVerse);
            const endVerseEl = findElement(drawEndVerse);

            if (startVerseEl && endVerseEl) {
                const containerRect = bibleTextContainer.getBoundingClientRect();
                const startRect = startVerseEl.getBoundingClientRect();
                const endRect = endVerseEl.getBoundingClientRect();

                const startPos = startRect.top - containerRect.top;
                const endPos = endRect.bottom - containerRect.top;
                segmentsToDraw.push({
                    start: drawStartVerse,
                    end: drawEndVerse,
                    startPos: startPos, // Store measurement
                    endPos: endPos      // Store measurement
                });
            }
        });

        if (segmentsToDraw.length === 0) return;

        // Use stored measurements for total bounds
        const totalStartPos = segmentsToDraw[0].startPos;
        const totalEndPos = segmentsToDraw[segmentsToDraw.length - 1].endPos;

        let slotIndex = 0;
        while (occupiedSlots.some(s => s.slotIndex === slotIndex && totalStartPos < s.end && totalEndPos > s.start)) {
            slotIndex++;
        }
        occupiedSlots.push({ start: totalStartPos, end: totalEndPos, slotIndex: slotIndex });

        positionalReadings.push({ reading, segmentsToDraw, totalStartPos, totalEndPos, slotIndex });
    });

    // Sort by position to make finding the "next" reading easier
    positionalReadings.sort((a, b) => a.totalStartPos - b.totalStartPos);

    // --- Step 2: Render each reading with calculated max heights (MUTATE PHASE) ---
    const fragment = document.createDocumentFragment(); // Use Fragment

    positionalReadings.forEach((posReading, index) => {
        const { reading, segmentsToDraw, totalStartPos, totalEndPos, slotIndex } = posReading;

        let maxLabelHeight = 9999;

        for (let i = index + 1; i < positionalReadings.length; i++) {
            const nextReading = positionalReadings[i];
            if (nextReading.slotIndex === slotIndex) {
                maxLabelHeight = nextReading.totalStartPos - totalStartPos;
                break;
            }
        }

        const startChapter = parseVerse((reading.segments || [{ start: reading.start }])[0].start).chapter;
        const endChapter = parseVerse((reading.segments || [{ end: reading.end }])[reading.segments ? reading.segments.length - 1 : 0].end).chapter;

        let labelText = reading.name;
        // Check if it spans chapters
        if (startChapter !== endChapter) {
            // If the start chapter is not the current one, it's a continuation
            if (currentChapterNum === startChapter) {
                labelText = `${reading.name} (cont...)`;
            }
            // If the end chapter is not the current one (or is 1000), it's a continuation
            else if (currentChapterNum === endChapter) {
                labelText = `(cont...) ${reading.name}`;
            }
            // If neither start nor end chapter matches, it's passing through
            else {
                labelText = `(cont...) ${reading.name} (cont...)`;
            }
        }

        let labelHasBeenShown = false;
        let lastSegmentEndPos = null; // --- ADDED FOR CONNECTORS ---

        segmentsToDraw.forEach((segment, segmentIndex) => {
            // Use stored measurements
            const startPos = segment.startPos;
            const endPos = segment.endPos;

            // --- NEW: Draw connecting line if this is not the first segment ---
            if (segmentIndex > 0 && lastSegmentEndPos !== null) {
                const connectorHeight = startPos - lastSegmentEndPos;
                // Only draw if there's a visible gap (e.g., > 1px)
                if (connectorHeight > 1) {
                    const connectorBar = document.createElement('div');
                    connectorBar.style.top = `${lastSegmentEndPos}px`;
                    connectorBar.style.height = `${connectorHeight}px`;
                    connectorBar.style.borderColor = reading.color; // Use the same color

                    if (isRightSided) {
                        connectorBar.className = 'annotation-bar-right annotation-bar-connector'; // New class
                        // --- FIX: Center the 1px connector in the 5px bar area ---
                        connectorBar.style.left = `${(slotIndex * 25) + 10 + 2}px`; // +2px
                    } else {
                        connectorBar.className = 'annotation-bar-left annotation-bar-connector'; // New class
                        // --- FIX: Center the 1px connector in the 5px bar area ---
                        connectorBar.style.right = `${(slotIndex * 25) + 10 + 2}px`; // +2px
                    }
                    fragment.appendChild(connectorBar);
                }
            }
            lastSegmentEndPos = endPos; // Update for the next iteration
            // --- END NEW ---

            const bar = document.createElement('div');
            bar.style.top = `${startPos}px`;
            bar.style.height = `${endPos - startPos}px`;
            // --- CHANGE: Use backgroundColor for rounded corners ---
            bar.style.backgroundColor = reading.color;

            if (!labelHasBeenShown) {
                const label = document.createElement('span');
                label.className = 'label';
                label.textContent = labelText;

                label.style.maxHeight = `${maxLabelHeight - 8}px`;
                bar.style.overflow = 'visible';
                bar.style.zIndex = '5';

                bar.appendChild(label);
                labelHasBeenShown = true;

                // --- Add hover event listeners to elevate z-index ---
                label.addEventListener('mouseenter', () => {
                    bar.style.zIndex = '1000'; // Bring to front
                });
                label.addEventListener('mouseleave', () => {
                    bar.style.zIndex = '5'; // Reset to default
                });
                // --- End hover event listeners ---

                // --- Add click event listener to copy text to clipboard ---
                label.addEventListener('click', async (e) => {
                    try {
                        await navigator.clipboard.writeText(labelText);

                        // Visual feedback: show "Copied!" text
                        const feedback = document.createElement('div');
                        feedback.textContent = 'Copied to clipboard';
                        feedback.style.position = 'absolute';
                        feedback.style.fontSize = '11px';
                        feedback.style.color = '#769879';
                        feedback.style.background = 'white';
                        feedback.style.padding = '2px 6px';
                        feedback.style.borderRadius = '3px';
                        feedback.style.boxShadow = '0 2px 4px rgba(0,0,0,0.2)';
                        feedback.style.zIndex = '1001';
                        feedback.style.pointerEvents = 'none';
                        feedback.style.transition = 'opacity 0.3s ease-out';

                        // Position below the label
                        const rect = label.getBoundingClientRect();
                        feedback.style.top = `${rect.bottom - rect.top + 5}px`;
                        feedback.style.left = '50%';
                        feedback.style.transform = 'translateX(-50%)';

                        label.appendChild(feedback);

                        // Fade out and remove
                        setTimeout(() => {
                            feedback.style.opacity = '0';
                            setTimeout(() => feedback.remove(), 300);
                        }, 1200);
                    } catch (err) {
                        console.error('Failed to copy text to clipboard:', err);
                    }
                });
                // --- End click event listener ---
            }

            if (isRightSided) {
                bar.className = 'annotation-bar-right';
                bar.style.left = `${(slotIndex * 25) + 10}px`;
            } else {
                bar.className = 'annotation-bar-left';
                bar.style.right = `${(slotIndex * 25) + 10}px`;
            }
            fragment.appendChild(bar);
        });
    });

    container.appendChild(fragment);
}


// --- REFERENCE POPUP FUNCTIONS ---

/**
 * Clears all existing reference pills from the document.
 * Called before redrawing (e.g., on translation switch).
 */
function clearRefPills() {
    document.querySelectorAll('.ref-pill').forEach(pill => pill.remove());
}

/**
 * Injects CCC and RM pills into the active translation's text.
 * @param {object | null} bookCccRefs - The CCC reference data for the current book.
 * @param {object | null} bookRmRefs - The RM reference data for the current book.
 * @param {number} chapterNum - The current chapter number.
 */
function injectRefPills(bookCccRefs, bookRmRefs, chapterNum) {
    const chapterStr = String(chapterNum);

    // Get refs for the current chapter
    const chapterCccRefs = bookCccRefs ? bookCccRefs[chapterStr] : null;
    const chapterRmRefs = bookRmRefs ? bookRmRefs[chapterStr] : null; // RM refs are {book: {chapter: {verse: []}}}

    if (!chapterCccRefs && !chapterRmRefs) {
        // No refs for this chapter
        return;
    }

    // Find all unique verse strings from both sources
    const allVerseStrs = new Set();
    if (chapterCccRefs) { Object.keys(chapterCccRefs).forEach(v => allVerseStrs.add(v)); }
    if (chapterRmRefs) { Object.keys(chapterRmRefs).forEach(v => allVerseStrs.add(v)); }

    // Find the currently active translation container
    const activeTranslation = document.querySelector('.translation-text.active');
    if (!activeTranslation) return;

    for (const verseStr of allVerseStrs) {
        const cccParaIds = (chapterCccRefs && chapterCccRefs[verseStr]) ? chapterCccRefs[verseStr] : [];
        const rmParaIds = (chapterRmRefs && chapterRmRefs[verseStr]) ? chapterRmRefs[verseStr] : [];

        if (cccParaIds.length === 0 && rmParaIds.length === 0) continue;

        const verseIdentifier = `${chapterStr}:${verseStr}`;

        // Use findElement to locate the verse element
        const verseElement = findElement(verseIdentifier);

        if (verseElement) {
            const pill = document.createElement('span');
            pill.className = 'ref-pill';

            // Set dataset for both
            pill.dataset.cccRefs = JSON.stringify(cccParaIds);
            pill.dataset.rmRefs = JSON.stringify(rmParaIds);

            // Set pill text
            if (cccParaIds.length > 0 && rmParaIds.length > 0) {
                pill.textContent = 'CCC / RM';
            } else if (cccParaIds.length > 0) {
                pill.textContent = 'CCC';
            } else {
                pill.textContent = 'RM';
            }

            pill.addEventListener('click', showRefPopup);

            // Append pill as the last child of the verse element
            verseElement.appendChild(pill);
        }
    }
}

/**
 * Handles the click event on a reference pill.
 * @param {Event} event - The click event.
 */
function showRefPopup(event) {
    event.stopPropagation(); // Stop click from bubbling up
    const pill = event.currentTarget;

    const cccParaIds = JSON.parse(pill.dataset.cccRefs);
    const rmParaIds = JSON.parse(pill.dataset.rmRefs);

    const originalText = pill.textContent;
    pill.textContent = '...'; // Show loading state

    // Determine which promises to run
    const cccPromise = (cccParaIds.length > 0) ? getCccTextData() : Promise.resolve(null);
    const rmPromise = (rmParaIds.length > 0) ? getRmTextData() : Promise.resolve(null);

    Promise.all([cccPromise, rmPromise])
        .then(([cccData, rmData]) => {
            buildAndShowRefModal(cccParaIds, cccData, rmParaIds, rmData);
            pill.textContent = originalText; // Reset pill text
        })
        .catch(err => {
            console.error("Failed to load reference text:", err);
            pill.textContent = originalText; // Reset on error
        });
}

/**
 * Lazy-loads the ccc-text.json file.
 * @returns {Promise<object>} A promise that resolves with the CCC text data.
 */
function getCccTextData() {
    // If data is already loaded, return it
    if (window.cccTextData) {
        return Promise.resolve(window.cccTextData);
    }

    // If we are already fetching, return the existing promise
    if (window.cccTextPromise) {
        return window.cccTextPromise;
    }

    // Start fetching the data
    console.log("Fetching ccc-text.json...");
    window.cccTextPromise = fetch('../data/ccc-text.json')
        .then(response => {
            if (!response.ok) throw new Error('Failed to load ccc-text.json');
            return response.json();
        })
        .then(data => {
            window.cccTextData = data; // Cache the data
            console.log("CCC text data loaded.");
            return data;
        })
        .catch(err => {
            window.cccTextPromise = null; // Clear promise on error
            throw err;
        });

    return window.cccTextPromise;
}

/**
 * Lazy-loads the roman-missal-text.json file.
 * @returns {Promise<object>} A promise that resolves with the RM text data.
 */
function getRmTextData() {
    // If data is already loaded, return it
    if (window.rmTextData) {
        return Promise.resolve(window.rmTextData);
    }

    // If we are already fetching, return the existing promise
    if (window.rmTextPromise) {
        return window.rmTextPromise;
    }

    // Start fetching the data
    console.log("Fetching roman-missal-text.json...");
    window.rmTextPromise = fetch('../data/roman-missal-text.json')
        .then(response => {
            if (!response.ok) throw new Error('Failed to load roman-missal-text.json');
            return response.json();
        })
        .then(data => {
            window.rmTextData = data; // Cache the data
            console.log("RM text data loaded.");
            return data;
        })
        .catch(err => {
            window.rmTextPromise = null; // Clear promise on error
            throw err;
        });

    return window.rmTextPromise;
}


/**
 * Builds and injects the Reference modal into the DOM.
 * @param {string[]} cccParaIds - Array of CCC paragraph IDs to display.
 * @param {object} cccData - The complete CCC text data.
 * @param {string[]} rmParaIds - Array of RM paragraph IDs to display.
 * @param {object} rmData - The complete RM text data.
 */
function buildAndShowRefModal(cccParaIds, cccData, rmParaIds, rmData) {
    // Close any existing modal first
    closeRefModal();

    let modalContent = '';

    // --- 1. Add CCC Content ---
    if (cccParaIds.length > 0 && cccData) {
        modalContent += '<h3 class="ref-modal-section-header">Catechism of the Catholic Church</h3>';

        cccParaIds.forEach((paraId, index) => {
            const paraData = cccData[paraId];
            if (paraData) {
                // Get the first and last headers
                const firstHeader = paraData.headers[0];
                const lastHeader = paraData.headers.slice(-1)[0];
                let displayHeader;

                if (firstHeader && lastHeader) {
                    // Check if they are the same (e.g., only one header in the array)
                    if (firstHeader === lastHeader) {
                        displayHeader = firstHeader;
                    } else {
                        // Combine first and last with a line break
                        displayHeader = `${firstHeader}<br>${lastHeader}`;
                    }
                } else {
                    // Default if headers array is empty
                    displayHeader = 'Catechism of the Catholic Church';
                }

                if (index > 0) {
                    modalContent += '<hr class="ref-divider">';
                }

                modalContent += `<div class="ref-paragraph-container">`;
                modalContent += `<h4 class="ref-header">${displayHeader}</h4>`;

                // Paragraph text with ID
                modalContent += `<p class="ref-text"><b>${paraId}</b> ${paraData.text}</p>`;

                // Footnotes
                if (paraData.footnotes && paraData.footnotes.length > 0) {
                    modalContent += `<ol class="ref-footnotes">`;
                    paraData.footnotes.forEach(fn => {
                        modalContent += `<li>${fn.text}</li>`;
                    });
                    modalContent += `</ol>`;
                }

                // Source link
                modalContent += `<a href="${paraData.source_url}" class="ref-source-link" target="_blank">CCC ${paraId} →</a>`;
                modalContent += `</div>`;
            }
        });
    }

    // --- 2. Add Divider ---
    if (cccParaIds.length > 0 && rmParaIds.length > 0) {
        modalContent += '<hr class="ref-divider-major">';
    }

    // --- 3. Add RM Content ---
    if (rmParaIds.length > 0 && rmData) {
        modalContent += '<h3 class="ref-modal-section-header">Roman Missal - Order of Mass</h3>';

        rmParaIds.forEach((paraId, index) => {
            const paraData = rmData[paraId];
            if (paraData) {
                if (index > 0) {
                    modalContent += '<hr class="ref-divider">';
                }

                modalContent += `<div class="ref-paragraph-container">`;

                // Get the last header
                const lastHeader = paraData.headers.slice(-1)[0];
                if (lastHeader) {
                    modalContent += `<h4 class="ref-header">${lastHeader}</h4>`;
                }

                // Paragraph text with ID
                // RM text already contains HTML, so just inject it
                modalContent += `<div class="ref-text"><b>${paraId}</b> ${paraData.text}</div>`;

                // Source link
                // modalContent += `<a href="${paraData.source_url}" class="ref-source-link" target="_blank">RM ${paraId} →</a>`;
                // modalContent += `</div>`;
            }
        });
    }


    // Create backdrop
    const backdrop = document.createElement('div');
    backdrop.id = 'ref-modal-backdrop';
    backdrop.addEventListener('click', closeRefModal);

    // Create modal
    const modal = document.createElement('div');
    modal.id = 'ref-modal';

    modal.innerHTML = `
        <div id="ref-modal-header">
            <button id="ref-modal-close">&times;</button>
        </div>
        <div id="ref-modal-content">
            ${modalContent}
        </div>
    `;

    document.body.appendChild(backdrop);
    document.body.appendChild(modal);

    // Add close listener
    modal.querySelector('#ref-modal-close').addEventListener('click', closeRefModal);

    // Add Esc key listener
    const handleEsc = (e) => {
        if (e.key === 'Escape') {
            closeRefModal();
        }
    };
    document.addEventListener('keydown', handleEsc);

    // Store the listener on the modal element so we can remove it later
    modal.dataset.escListener = 'true';
    // (Note: Removing anonymous listeners is tricky, so we'll handle removal in closeRefModal by checking if it exists, 
    // or better, define the function outside or attach it to the modal and check in closeRefModal.
    // Simpler approach: Just add it here, and in closeRefModal remove it. 
    // To remove it, we need a reference. Let's attach it to the window object temporarily or use a named function.)

    window.currentRefModalEscHandler = handleEsc;
}

/**
 * Removes the Reference modal and backdrop from the DOM.
 */
function closeRefModal() {
    document.getElementById('ref-modal')?.remove();
    document.getElementById('ref-modal-backdrop')?.remove();

    if (window.currentRefModalEscHandler) {
        document.removeEventListener('keydown', window.currentRefModalEscHandler);
        window.currentRefModalEscHandler = null;
    }
}


// --- BIBLE NAVIGATION MODAL LOGIC ---

// 1. Bible Data Structure (Catholic Canon)
const BIBLE_NAV_DATA = [
    // Pentateuch (Law)
    { name: "Genesis", slug: "genesis", abbr: "Gen", ch: 50, section: "law" },
    { name: "Exodus", slug: "exodus", abbr: "Ex", ch: 40, section: "law" },
    { name: "Leviticus", slug: "leviticus", abbr: "Lev", ch: 27, section: "law" },
    { name: "Numbers", slug: "numbers", abbr: "Num", ch: 36, section: "law" },
    { name: "Deuteronomy", slug: "deuteronomy", abbr: "Dt", ch: 34, section: "law" },
    // History
    { name: "Joshua", slug: "joshua", abbr: "Jos", ch: 24, section: "hist" },
    { name: "Judges", slug: "judges", abbr: "Jgs", ch: 21, section: "hist" },
    { name: "Ruth", slug: "ruth", abbr: "Ru", ch: 4, section: "hist" },
    { name: "1 Samuel", slug: "1-samuel", abbr: "1Sm", ch: 31, section: "hist" },
    { name: "2 Samuel", slug: "2-samuel", abbr: "2Sm", ch: 24, section: "hist" },
    { name: "1 Kings", slug: "1-kings", abbr: "1Kgs", ch: 22, section: "hist" },
    { name: "2 Kings", slug: "2-kings", abbr: "2Kgs", ch: 25, section: "hist" },
    { name: "1 Chronicles", slug: "1-chronicles", abbr: "1Chr", ch: 29, section: "hist" },
    { name: "2 Chronicles", slug: "2-chronicles", abbr: "2Chr", ch: 36, section: "hist" },
    { name: "Ezra", slug: "ezra", abbr: "Ezr", ch: 10, section: "hist" },
    { name: "Nehemiah", slug: "nehemiah", abbr: "Neh", ch: 13, section: "hist" },
    { name: "Tobit", slug: "tobit", abbr: "Tb", ch: 14, section: "hist" },
    { name: "Judith", slug: "judith", abbr: "Jdt", ch: 16, section: "hist" },
    { name: "Esther", slug: "esther", abbr: "Est", ch: 10, section: "hist" },
    { name: "1 Maccabees", slug: "1-maccabees", abbr: "1Mc", ch: 16, section: "hist" },
    { name: "2 Maccabees", slug: "2-maccabees", abbr: "2Mc", ch: 15, section: "hist" },
    // Wisdom
    { name: "Job", slug: "job", abbr: "Jb", ch: 42, section: "wis" },
    { name: "Psalms", slug: "psalms", abbr: "Ps", ch: 150, section: "wis" },
    { name: "Proverbs", slug: "proverbs", abbr: "Prv", ch: 31, section: "wis" },
    { name: "Ecclesiastes", slug: "ecclesiastes", abbr: "Eccl", ch: 12, section: "wis" },
    { name: "Song of Songs", slug: "song-of-songs", abbr: "Sg", ch: 8, section: "wis" },
    { name: "Wisdom", slug: "wisdom", abbr: "Wis", ch: 19, section: "wis" },
    { name: "Sirach", slug: "sirach", abbr: "Sir", ch: 51, section: "wis" },
    // Prophets
    { name: "Isaiah", slug: "isaiah", abbr: "Is", ch: 66, section: "prop" },
    { name: "Jeremiah", slug: "jeremiah", abbr: "Jer", ch: 52, section: "prop" },
    { name: "Lamentations", slug: "lamentations", abbr: "Lam", ch: 5, section: "prop" },
    { name: "Baruch", slug: "baruch", abbr: "Bar", ch: 6, section: "prop" },
    { name: "Ezekiel", slug: "ezekiel", abbr: "Ez", ch: 48, section: "prop" },
    { name: "Daniel", slug: "daniel", abbr: "Dn", ch: 14, section: "prop" },
    { name: "Hosea", slug: "hosea", abbr: "Hos", ch: 14, section: "prop" },
    { name: "Joel", slug: "joel", abbr: "Jl", ch: 4, section: "prop" },
    { name: "Amos", slug: "amos", abbr: "Am", ch: 9, section: "prop" },
    { name: "Obadiah", slug: "obadiah", abbr: "Ob", ch: 1, section: "prop" },
    { name: "Jonah", slug: "jonah", abbr: "Jon", ch: 4, section: "prop" },
    { name: "Micah", slug: "micah", abbr: "Mi", ch: 7, section: "prop" },
    { name: "Nahum", slug: "nahum", abbr: "Na", ch: 3, section: "prop" },
    { name: "Habakkuk", slug: "habakkuk", abbr: "Hb", ch: 3, section: "prop" },
    { name: "Zephaniah", slug: "zephaniah", abbr: "Zep", ch: 3, section: "prop" },
    { name: "Haggai", slug: "haggai", abbr: "Hg", ch: 2, section: "prop" },
    { name: "Zechariah", slug: "zechariah", abbr: "Zec", ch: 14, section: "prop" },
    { name: "Malachi", slug: "malachi", abbr: "Mal", ch: 3, section: "prop" },
    // Gospels
    { name: "Matthew", slug: "matthew", abbr: "Mt", ch: 28, section: "gosp" },
    { name: "Mark", slug: "mark", abbr: "Mk", ch: 16, section: "gosp" },
    { name: "Luke", slug: "luke", abbr: "Lk", ch: 24, section: "gosp" },
    { name: "John", slug: "john", abbr: "Jn", ch: 21, section: "gosp" },
    { name: "Acts", slug: "acts", abbr: "Acts", ch: 28, section: "hist-nt" },
    // Epistles (Pauline)
    { name: "Romans", slug: "romans", abbr: "Rom", ch: 16, section: "epist" },
    { name: "1 Corinthians", slug: "1-corinthians", abbr: "1Cor", ch: 16, section: "epist" },
    { name: "2 Corinthians", slug: "2-corinthians", abbr: "2Cor", ch: 13, section: "epist" },
    { name: "Galatians", slug: "galatians", abbr: "Gal", ch: 6, section: "epist" },
    { name: "Ephesians", slug: "ephesians", abbr: "Eph", ch: 6, section: "epist" },
    { name: "Philippians", slug: "philippians", abbr: "Phil", ch: 4, section: "epist" },
    { name: "Colossians", slug: "colossians", abbr: "Col", ch: 4, section: "epist" },
    { name: "1 Thessalonians", slug: "1-thessalonians", abbr: "1Thes", ch: 5, section: "epist" },
    { name: "2 Thessalonians", slug: "2-thessalonians", abbr: "2Thes", ch: 3, section: "epist" },
    { name: "1 Timothy", slug: "1-timothy", abbr: "1Tm", ch: 6, section: "epist" },
    { name: "2 Timothy", slug: "2-timothy", abbr: "2Tm", ch: 4, section: "epist" },
    { name: "Titus", slug: "titus", abbr: "Ti", ch: 3, section: "epist" },
    { name: "Philemon", slug: "philemon", abbr: "Phlm", ch: 1, section: "epist" },
    { name: "Hebrews", slug: "hebrews", abbr: "Heb", ch: 13, section: "epist" },
    // Catholic Epistles
    { name: "James", slug: "james", abbr: "Jas", ch: 5, section: "epist" },
    { name: "1 Peter", slug: "1-peter", abbr: "1Pt", ch: 5, section: "epist" },
    { name: "2 Peter", slug: "2-peter", abbr: "2Pt", ch: 3, section: "epist" },
    { name: "1 John", slug: "1-john", abbr: "1Jn", ch: 5, section: "epist" },
    { name: "2 John", slug: "2-john", abbr: "2Jn", ch: 1, section: "epist" },
    { name: "3 John", slug: "3-john", abbr: "3Jn", ch: 1, section: "epist" },
    { name: "Jude", slug: "jude", abbr: "Jude", ch: 1, section: "epist" },
    { name: "Revelation", slug: "revelation", abbr: "Rv", ch: 22, section: "prop-nt" }
];

// 2. Navigation Controller
function initNavigationModal() {
    const headerTitle = document.querySelector('.header-chapter');
    if (!headerTitle) return;

    // Make header interactive
    headerTitle.style.cursor = 'pointer';
    headerTitle.title = "Click to navigate";

    headerTitle.addEventListener('click', () => {
        openNavModal();
    });
}

function openNavModal() {
    // Remove existing if any
    const existing = document.getElementById('nav-modal');
    if (existing) existing.remove();

    const backdrop = document.createElement('div');
    backdrop.id = 'nav-modal-backdrop';
    backdrop.addEventListener('click', closeNavModal);

    const modal = document.createElement('div');
    modal.id = 'nav-modal';
    modal.innerHTML = `
        <div id="nav-modal-header">
            <h3 id="nav-modal-title">Select Book</h3>
        </div>
        <div id="nav-modal-content"></div>
    `;

    document.body.appendChild(backdrop);
    document.body.appendChild(modal);

    renderBookGrid();
}

function closeNavModal() {
    const modal = document.getElementById('nav-modal');
    const backdrop = document.getElementById('nav-modal-backdrop');
    if (modal) modal.remove();
    if (backdrop) backdrop.remove();
}

function renderBookGrid() {
    const container = document.getElementById('nav-modal-content');
    const title = document.getElementById('nav-modal-title');
    if (!container) return;

    title.innerHTML = '';

    container.innerHTML = '';
    container.className = 'nav-grid-books';

    BIBLE_NAV_DATA.forEach(book => {
        const btn = document.createElement('button');
        // Added 'square' class for styling
        btn.className = `nav-item square nav-section-${book.section}`;
        btn.textContent = book.abbr;
        btn.title = book.name;

        btn.addEventListener('click', () => {
            renderChapterGrid(book);
        });

        container.appendChild(btn);
    });
}

function renderChapterGrid(bookData) {
    const container = document.getElementById('nav-modal-content');
    const title = document.getElementById('nav-modal-title');
    if (!container) return;

    container.innerHTML = '';
    container.className = 'nav-grid-chapters';

    for (let i = 1; i <= bookData.ch; i++) {
        const btn = document.createElement('button');
        btn.className = `nav-item square nav-chapter-item`;
        btn.textContent = i;

        btn.addEventListener('click', () => {
            navigateToChapter(bookData.slug, i);
        });

        container.appendChild(btn);
    }
}

function navigateToChapter(bookSlug, chapterNum) {
    // Pad chapter number with leading zero if < 10
    const paddedChapter = String(chapterNum).padStart(2, '0');

    // Assuming structure is /bible/[slug]-[chapter].html
    // If script is running in a file like /bible/1-chronicles-01.html, 
    // we can simply link relative to the current folder.
    window.location.href = `${bookSlug}-${paddedChapter}.html`;
}

// 3. Initialize on Load (Append this to your existing window.onload logic or just call it here)
window.addEventListener('load', () => {
    initNavigationModal();
});