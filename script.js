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

window.addEventListener('load', () => {
    const body = document.body;
    const book = body.dataset.book;
    const chapter = body.dataset.chapter;

    if (!book || !chapter) {
        console.error("Book or chapter not defined in body data attributes.");
        return;
    }

    let lectionaryReadingsData = [];
    let divineOfficeData = [];

    const redraw = () => drawAnnotations(lectionaryReadingsData, divineOfficeData);

    // --- Translation Switcher Logic ---
    const switcher = document.getElementById('translation-switcher');
    if (switcher) {
        // Set initial value from localStorage if it exists
        const savedTranslation = localStorage.getItem('selectedTranslation');
        if (savedTranslation) {
            switcher.value = savedTranslation;
        }

        // Function to apply the selected translation
        const applyTranslation = () => {
            const selectedValue = switcher.value;
            document.querySelectorAll('.translation-text').forEach(div => {
                div.classList.remove('active');
            });
            const selectedTranslationDiv = document.querySelector(`.translation-text.${selectedValue}`);
            if (selectedTranslationDiv) {
                selectedTranslationDiv.classList.add('active');
            }
            localStorage.setItem('selectedTranslation', selectedValue); // Save user's choice
            redraw(); // Redraw annotations for the new layout
        };

        switcher.addEventListener('change', applyTranslation);
        // Apply the initial translation on page load
        applyTranslation();
    }
    
    // --- ARROW KEY NAVIGATION ---
    document.addEventListener('keydown', function(event) {
        // Find the previous and next links in the bottom navigation
        const prevLink = document.querySelector('.bottom-nav a:first-of-type');
        const nextLink = document.querySelector('.bottom-nav a:last-of-type');

        if (event.key === 'ArrowLeft') {
            if (prevLink && prevLink.href) {
                prevLink.click();
            }
        } else if (event.key === 'ArrowRight') {
            if (nextLink && nextLink.href) {
                nextLink.click();
            }
        }
    });

    const currentChapterNum = parseInt(chapter, 10);

    const parseVerse = (verseStr) => {
        const [c, v] = verseStr.split(/[:a-z]/).map(Number); // Regex handles 'a', 'b', etc.
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
            redraw(); // Initial draw after data is fetched
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
        
        const containerTop = bibleTextContainer.offsetTop;
        const totalStartPos = firstDrawEl.offsetTop - containerTop;
        const totalEndPos = lastDrawEl.offsetTop + lastDrawEl.offsetHeight - containerTop;

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

            const containerTop = bibleTextContainer.offsetTop;
            const startPos = startVerseEl.offsetTop - containerTop;
            const endPos = endVerseEl.offsetTop + endVerseEl.offsetHeight - containerTop;
            
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

