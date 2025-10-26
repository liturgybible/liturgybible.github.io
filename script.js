/**
 * Helper function to find a verse element within the currently active translation.
 * @param {string} verseIdentifier - The verse to find (e.g., "1:5a" or "1:5").
 * @returns {HTMLElement|null} The found element or null.
 */
function findElement(verseIdentifier) {
    // Only search within the visible .translation-text.active container
    let element = document.querySelector(`.translation-text.active [data-verse-part="${verseIdentifier}"]`);
    if (!element) {
        element = document.querySelector(`.translation-text.active [data-verse="${verseIdentifier}"]`);
    }
    return element;
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
    const readingDate = new Date(readingsData.date + 'T00:00:00');

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
    popupContent += `<p class="popup-date">${formatDisplayDate(readingDate)}</p>`;
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

    const closeButton = popupDiv.querySelector('.popup-close-btn');
    if (closeButton) {
        closeButton.addEventListener('click', () => {
            popupDiv.style.display = 'none';
        });
    }
}

/**
 * --- UPDATED: Highlights verses by drawing a continuous block ---
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
            // --- MODIFICATION HERE ---
            const padding = 4; // 4px padding
            // Measure positions relative to the bibleTextContainer
            const startPos = startEl.offsetTop - padding; // Move up by 4px
            const endPos = endEl.offsetTop + endEl.offsetHeight + padding; // Move down by 4px
            const height = endPos - startPos; // Recalculate height
            // --- END MODIFICATION ---

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
    
    let todaysReadingsData = null; // Store today's readings to pass to other functions

    // --- Daily Readings Popup Logic ---
    const todayStr = getCurrentDateString();
    fetch('../data_usccb/usccb-readings.json')
        .then(response => {
            if (!response.ok) throw new Error('Failed to load readings data');
            return response.json();
        })
        .then(allReadings => {
            todaysReadingsData = allReadings.find(reading => reading.date === todayStr);
            if (todaysReadingsData) {
                displayReadingsPopup(todaysReadingsData);
                // Also highlight readings on load
                if (book && chapter) {
                    highlightDailyReadings(todaysReadingsData);
                }
            } else {
                console.log("No readings found for today:", todayStr);
            }
        })
        .catch(error => {
            console.error("Error fetching or processing daily readings:", error);
        });
    // --- End Daily Readings Popup Logic ---

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
        highlightDailyReadings(todaysReadingsData);
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

        const allVersesOnPage = document.querySelectorAll(`.translation-text.active p[data-verse^="${currentChapterNum}:"]`);
        if (allVersesOnPage.length === 0) return;
        
        const firstVerseOnPage = allVersesOnPage[0].dataset.verse;
        const lastVerseOnPage = allVersesOnPage[allVersesOnPage.length - 1].dataset.verse;

        const segmentsToDraw = [];
        originalSegments.forEach(segment => {
            const segStart = parseVerse(segment.start);
            const segEnd = parseVerse(segment.end);
            if (currentChapterNum < segStart.chapter || currentChapterNum > segEnd.chapter) return;
            let drawStartVerse = segStart.chapter < currentChapterNum ? firstVerseOnPage : segment.start;
            let drawEndVerse = segEnd.chapter > currentChapterNum ? lastVerseOnPage : segment.end;
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
        if (startChapter !== endChapter) {
            if (currentChapterNum === startChapter) {
                labelText = `${reading.name} (cont...)`;
            } else if (currentChapterNum === endChapter) {
                labelText = `(cont...) ${reading.name}`;
            } else {
                labelText = `(cont...) ${reading.name} (cont...)`;
            }
        }
        
        let labelHasBeenShown = false;
        segmentsToDraw.forEach(segment => {
            const startVerseEl = findElement(segment.start);
            const endVerseEl = findElement(segment.end);
            if (!startVerseEl || !endVerseEl) return;

            const startPos = startVerseEl.offsetTop;
            const endPos = endVerseEl.offsetTop + endVerseEl.offsetHeight;
            
            const bar = document.createElement('div');
            bar.style.top = `${startPos}px`;
            bar.style.height = `${endPos - startPos}px`;
            bar.style.borderColor = reading.color;

            if (!labelHasBeenShown) {
                const label = document.createElement('span');
                label.className = 'label';
                label.textContent = labelText;
                
                label.style.maxHeight = `${maxLabelHeight - 8}px`; 
                bar.style.overflow = 'visible';
                bar.style.zIndex = '5'; 
                
                bar.appendChild(label);
                labelHasBeenShown = true;

                // --- HOVER LOGIC (Attach to the first bar segment) ---
                bar.addEventListener('mouseenter', () => {
                    label.style.maxHeight = 'none';
                    label.style.writingMode = 'horizontal-tb';
                    label.style.transform = 'none';
                    label.style.whiteSpace = 'normal';
                    label.style.overflow = 'visible';
                    label.style.width = '200px';
                    label.style.backgroundColor = '#fffff7'; // Light parchment
                    label.style.border = `1px solid ${reading.color}`;
                    label.style.padding = '5px 8px';
                    label.style.borderRadius = '4px';
                    label.style.boxShadow = '0 3px 10px rgba(0,0,0,0.2)';
                    label.style.zIndex = '10';
                    
                    if (isRightSided) {
                        label.style.left = '25px';
                    } else {
                        label.style.right = '25px';
                    }
                });

                bar.addEventListener('mouseleave', () => {
                    // Reset all styles
                    label.style.maxHeight = `${maxLabelHeight - 8}px`;
                    label.style.writingMode = '';
                    label.style.transform = '';
                    label.style.whiteSpace = '';
                    label.style.overflow = '';
                    label.style.width = '';
                    label.style.backgroundColor = '';
                    label.style.border = '';
                    label.style.padding = '';
                    label.style.borderRadius = '';
                    label.style.boxShadow = '';
                    label.style.zIndex = '';
                    label.style.left = '';
                    label.style.right = '';
                });
                // --- END HOVER LOGIC ---
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

