/**
 * Helper function to find a verse element within the currently active translation.
 * @param {string} verseIdentifier - The verse to find (e.g., "1:5a" or "1:5").
 * @returns {HTMLElement|null} The found element or null.
 */
function findElement(verseIdentifier) {
    const activeTranslation = document.querySelector('.translation-text.active');
    if (!activeTranslation) return null;

    // 1. Try to find the exact verse part (e.g., "8:31b")
    let element = activeTranslation.querySelector(`[data-verse-part="${verseIdentifier}"]`);
    if (element) {
        return element;
    }

    // 2. Try to find the exact whole verse (e.g., "8:39")
    element = activeTranslation.querySelector(`[data-verse="${verseIdentifier}"]`);
    if (element) {
        return element;
    }

    // 3. Fallback: If looking for a verse part (e.g., "1:1b") and it's not found,
    //    try to find the whole verse element (e.g., "1:1").
    const partMatch = verseIdentifier.match(/^(\d+:\d+)[a-z]$/); // Matches "1:1b", "1:1c", etc.
    if (partMatch) {
        const wholeVerseIdentifier = partMatch[1]; // "1:1"
        element = activeTranslation.querySelector(`[data-verse="${wholeVerseIdentifier}"]`);
        if (element) {
            return element;
        }
    }
    
    // 4. Fallback: If looking for a whole verse (e.g. "1:1") and it's not found,
    //    maybe it's split into parts in the HTML? Try to find the first part (e.g. "1:1a").
    element = activeTranslation.querySelector(`[data-verse-part="${verseIdentifier}a"]`);
    if (element) {
         return element;
    }

    return null; // No match found
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
             readingSequence.push({ ref: readingRef, link: readingLink, label: label});
        }
    };

    // Populate the sequence first
    addReadingToSequence('Reading 1', readingsData.reading_1, readingsData.reading_1_link);
    addReadingToSequence('Psalm', readingsData.psalm, readingsData.psalm_link);
    addReadingToSequence('Reading 2', readingsData.reading_2, readingsData.reading_2_link);
    addReadingToSequence('Alleluia', readingsData.allelulia, readingsData.allelulia_link);
    addReadingToSequence('Gospel', readingsData.gospel, readingsData.gospel_link);

    // --- Build Popup Content ---
    popupContent += `<div class="popup-header">`;
    popupContent += `<div>`; 
    popupContent += `<h4>${readingsData.name || 'Daily Readings'}</h4>`;
    popupContent += `<input type="date" class="popup-date-picker" value="${dateValue}">`;
    popupContent += `</div>`;
    popupContent += `<button class="popup-close-btn">&times;</button>`;
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
function highlightDailyReadings(todaysReadings) {
    const bibleTextContainer = document.querySelector('.bible-text');
    
    // 1. Clear any existing highlights
    document.querySelectorAll('.daily-reading-highlight-block').forEach(el => {
        el.remove();
    });

    const body = document.body;
    const currentBookSlug = body.dataset.book;
    const currentChapterNum = parseInt(body.dataset.chapter, 10);

    if (!todaysReadings || !currentBookSlug || isNaN(currentChapterNum) || !bibleTextContainer) {
        return; // Not a chapter page or no data
    }

    // 2. Build a list of applicable ranges for this specific page
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
        return; // No readings for this chapter today
    }
    
    // 3. Find all verse elements on the page (for calculations)
    const allVersesOnPage = document.querySelectorAll(`.translation-text.active p[data-verse^="${currentChapterNum}:"], .translation-text.active span[data-verse-part^="${currentChapterNum}:"]`);
    if (allVersesOnPage.length === 0) return;
    
    const firstVerseOnPage = allVersesOnPage[0].dataset.verse || allVersesOnPage[0].dataset.versePart;
    const lastVerseOnPage = allVersesOnPage[allVersesOnPage.length - 1].dataset.verse || allVersesOnPage[allVersesOnPage.length - 1].dataset.versePart;

    // 4. Iterate through ranges and draw highlight blocks
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
            const padding = 4; // 4px padding
            // Measure positions relative to the bibleTextContainer
            const startPos = startEl.offsetTop - padding; // Move up by 4px
            const endPos = endEl.offsetTop + endEl.offsetHeight + padding; // Move down by 4px
            const height = endPos - startPos; 

            const highlightBlock = document.createElement('div');
            highlightBlock.className = 'daily-reading-highlight-block';
            highlightBlock.style.top = startPos + 'px';
            highlightBlock.style.height = height + 'px';
            
            bibleTextContainer.appendChild(highlightBlock);
        }
    });
}


// --- MAIN SCRIPT EXECUTION ON LOAD ---
window.addEventListener('load', () => {
    const body = document.body;
    const book = body.dataset.book;
    const chapter = body.dataset.chapter;
    
    // --- Make readings data globally accessible ---
    window.todaysReadingsData = null; // Store today's readings to pass to other functions
    window.allUsccbReadings = []; // Store all readings
    
    // --- CCC Data ---
    window.bookCccRefs = null; // Store per-book CCC refs
    window.cccTextData = null; // Lazy-loaded full CCC text
    window.cccTextPromise = null; // Promise to manage lazy-loading

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
                // This is now handled in applyTranslationOnLoad
            })
            .catch(error => console.error("Error fetching CCC references:", error));
    }
    // --- End CCC Reference Logic ---


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
        drawAnnotations(lectionaryReadingsData, divineOfficeData);
        // Also re-highlight readings when redrawing (e.g., on translation switch)
        highlightDailyReadings(window.todaysReadingsData);
        
        // --- CCC: Clear and re-inject pills ---
        clearCccPills();
        if (window.bookCccRefs && chapter) {
            injectCccPills(window.bookCccRefs, parseInt(chapter, 10));
        }
    };

    // --- Translation Switcher Logic ---
    const switcher = document.getElementById('translation-switcher');
    if (switcher) {
        const savedTranslation = localStorage.getItem('selectedTranslation');
        if (savedTranslation) {
            switcher.value = savedTranslation;
        }

        const applyTranslation = () => {
            const selectedValue = switcher.value;
            document.querySelectorAll('.translation-text').forEach(div => {
                div.classList.remove('active');
            });
            const selectedTranslationDiv = document.querySelector(`.translation-text.${selectedValue}`);
            if (selectedTranslationDiv) {
                selectedTranslationDiv.classList.add('active');
            }
            localStorage.setItem('selectedTranslation', selectedValue); 
            redraw(); // Redraw annotations AND highlights
        };

        switcher.addEventListener('change', applyTranslation);
        // applyTranslation(); // Don't call here, call in the fetch success
    }
    
    // --- ARROW KEY NAVIGATION ---
    document.addEventListener('keydown', function(event) {
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
            
            // Apply initial translation and draw annotations/highlights
            const applyTranslationOnLoad = () => {
                const selectedValue = switcher ? switcher.value : 'dra'; // Default to 'dra' if no switcher
                document.querySelectorAll('.translation-text').forEach(div => {
                    div.classList.remove('active');
                });
                let selectedTranslationDiv = document.querySelector(`.translation-text.${selectedValue}`);
                if (!selectedTranslationDiv) { // Fallback to the first translation if saved one isn't found
                    selectedTranslationDiv = document.querySelector('.translation-text');
                    if (selectedTranslationDiv) selectedTranslationDiv.classList.add('active');
                }
                if (selectedTranslationDiv) selectedTranslationDiv.classList.add('active');
                
                // Now that translation is active, redraw annotations and highlights
                redraw(); 
            };
            applyTranslationOnLoad(); // Call the combined function
            
            window.addEventListener('resize', redraw);
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

    // --- Step 1: Calculate positions and slots for all readings ---
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

            segmentsToDraw.push({ start: drawStartVerse, end: drawEndVerse });
        });

        if (segmentsToDraw.length === 0) return;

        const firstDrawEl = findElement(segmentsToDraw[0].start);
        const lastDrawEl = findElement(segmentsToDraw[segmentsToDraw.length - 1].end);
        if (!firstDrawEl || !lastDrawEl) return;
        
        // --- Use offsetTop *relative to the bibleTextContainer* ---
        const totalStartPos = firstDrawEl.offsetTop;
        const totalEndPos = lastDrawEl.offsetTop + lastDrawEl.offsetHeight;

        let slotIndex = 0;
        while (occupiedSlots.some(s => s.slotIndex === slotIndex && totalStartPos < s.end && totalEndPos > s.start)) {
            slotIndex++;
        }
        occupiedSlots.push({ start: totalStartPos, end: totalEndPos, slotIndex: slotIndex });
        
        positionalReadings.push({ reading, segmentsToDraw, totalStartPos, totalEndPos, slotIndex });
    });

    // Sort by position to make finding the "next" reading easier
    positionalReadings.sort((a, b) => a.totalStartPos - b.totalStartPos);

    // --- Step 2: Render each reading with calculated max heights ---
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
            const startVerseEl = findElement(segment.start);
            const endVerseEl = findElement(segment.end);
            if (!startVerseEl || !endVerseEl) return;

            const startPos = startVerseEl.offsetTop;
            const endPos = endVerseEl.offsetTop + endVerseEl.offsetHeight;
            
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
                    container.appendChild(connectorBar);
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

                // --- REMOVED JAVASCRIPT HOVER LOGIC ---
                // All hover logic is now handled by CSS
            }

            if (isRightSided) {
                bar.className = 'annotation-bar-right';
                bar.style.left = `${(slotIndex * 25) + 10}px`;
            } else {
                bar.className = 'annotation-bar-left';
                bar.style.right = `${(slotIndex * 25) + 10}px`;
            }
            container.appendChild(bar);
        });
    });
}


// --- CCC POPUP FUNCTIONS ---

/**
 * Clears all existing CCC pills from the document.
 * Called before redrawing (e.g., on translation switch).
 */
function clearCccPills() {
    document.querySelectorAll('.ccc-pill').forEach(pill => pill.remove());
}

/**
 * Injects CCC pills into the active translation's text.
 * @param {object} bookCccRefs - The reference data for the current book.
 * @param {number} chapterNum - The current chapter number.
 */
function injectCccPills(bookCccRefs, chapterNum) {
    if (!bookCccRefs) return;
    
    const chapterStr = String(chapterNum);
    const chapterRefs = bookCccRefs[chapterStr];
    
    if (!chapterRefs) {
        // No refs for this chapter
        return;
    }
    
    // Find the currently active translation container
    const activeTranslation = document.querySelector('.translation-text.active');
    if (!activeTranslation) return;

    for (const verseStr in chapterRefs) {
        const paraIds = chapterRefs[verseStr]; // e.g., ["289", "337"]
        if (!paraIds || paraIds.length === 0) continue;
        
        const verseIdentifier = `${chapterStr}:${verseStr}`;
        
        // Use findElement to locate the verse element
        const verseElement = findElement(verseIdentifier);
        
        if (verseElement) {
            const pill = document.createElement('span');
            pill.className = 'ccc-pill';
            pill.textContent = 'CCC';
            pill.dataset.refs = JSON.stringify(paraIds);
            
            pill.addEventListener('click', showCccPopup);
            
            // Append pill as the last child of the verse element
            verseElement.appendChild(pill);
        }
    }
}

/**
 * Handles the click event on a CCC pill.
 * @param {Event} event - The click event.
 */
function showCccPopup(event) {
    event.stopPropagation(); // Stop click from bubbling up
    const pill = event.currentTarget;
    const paraIds = JSON.parse(pill.dataset.refs);
    
    pill.textContent = '...'; // Show loading state
    
    getCccTextData()
        .then(cccData => {
            buildAndShowCccModal(paraIds, cccData);
            pill.textContent = 'CCC'; // Reset pill text
        })
        .catch(err => {
            console.error("Failed to load CCC text:", err);
            pill.textContent = 'CCC'; // Reset on error
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
 * Builds and injects the CCC modal into the DOM.
 * @param {string[]} paraIds - Array of paragraph IDs to display.
 * @param {object} cccData - The complete CCC text data.
 */
function buildAndShowCccModal(paraIds, cccData) {
    // Close any existing modal first
    closeCccModal();
    
    let modalContent = '';
    
    paraIds.forEach((paraId, index) => {
        const paraData = cccData[paraId];
        if (paraData) {
            // Get the last (most specific) header
            const header = paraData.headers.slice(-1)[0] || 'Catechism of the Catholic Church';
            
            if (index > 0) {
                 modalContent += '<hr class="ccc-divider">';
            }
            
            modalContent += `<div class="ccc-paragraph-container">`;
            modalContent += `<h4 class="ccc-header">${header}</h4>`;
            
            // Paragraph text with ID
            modalContent += `<p class="ccc-text"><b>${paraId}</b> ${paraData.text}</p>`;
            
            // Footnotes
            if (paraData.footnotes && paraData.footnotes.length > 0) {
                modalContent += `<ol class="ccc-footnotes">`;
                paraData.footnotes.forEach(fn => {
                    modalContent += `<li>${fn.text}</li>`;
                });
                modalContent += `</ol>`;
            }
            
            // Source link
            modalContent += `<a href="${paraData.source_url}" class="ccc-source-link" target="_blank">CCC ${paraId} →</a>`;
            modalContent += `</div>`;
        }
    });

    // Create backdrop
    const backdrop = document.createElement('div');
    backdrop.id = 'ccc-modal-backdrop';
    backdrop.addEventListener('click', closeCccModal);
    
    // Create modal
    const modal = document.createElement('div');
    modal.id = 'ccc-modal';
    
    modal.innerHTML = `
        <div id="ccc-modal-header">
            <button id="ccc-modal-close">&times;</button>
        </div>
        <div id="ccc-modal-content">
            ${modalContent}
        </div>
    `;
    
    document.body.appendChild(backdrop);
    document.body.appendChild(modal);
    
    // Add close listener
    modal.querySelector('#ccc-modal-close').addEventListener('click', closeCccModal);
}

/**
 * Removes the CCC modal and backdrop from the DOM.
 */
function closeCccModal() {
    document.getElementById('ccc-modal')?.remove();
    document.getElementById('ccc-modal-backdrop')?.remove();
}