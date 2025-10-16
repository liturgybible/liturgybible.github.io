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

    // --- NEW: Translation Switcher Logic ---
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
    // --- END NEW LOGIC ---

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

        const startChapter = parseVerse(originalSegments[0].start).chapter;
        const endChapter = parseVerse(originalSegments[originalSegments.length - 1].end).chapter;
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
                bar.appendChild(label);
                labelHasBeenShown = true;
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
