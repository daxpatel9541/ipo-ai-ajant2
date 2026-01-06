function handleEnter(event) {
    if (event.key === 'Enter') {
        searchIPO();
    }
}

async function searchIPO() {
    const name = document.getElementById('ipoInput').value.trim();
    if (!name) {
        alert('Please enter an IPO name');
        return;
    }

    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';

    try {
        const response = await fetch(`/ipo?name=${encodeURIComponent(name)}`);
        if (!response.ok) {
            throw new Error('IPO not found');
        }

        const data = await response.json();
        displayIPOData(data);
        document.getElementById('results').style.display = 'block';
    } catch (error) {
        alert('IPO not found in database. Please try another name.');
    } finally {
        document.getElementById('loading').style.display = 'none';
    }
}

function displayIPOData(data) {
    document.getElementById('ipo-name').textContent = data.ipo_name;
    document.getElementById('status').textContent = data.status;
    document.getElementById('gmp').textContent = data.gmp;
    document.getElementById('price-high').textContent = data.price_high;
    document.getElementById('issue-size').textContent = data.issue_size;
    document.getElementById('retail-sub').textContent = data.retail_subscription;
    document.getElementById('hni-sub').textContent = data.hni_subscription;
    document.getElementById('qib-sub').textContent = data.qib_subscription;
    document.getElementById('listing-gain').textContent = data.listing_gain;
    document.getElementById('best-category').textContent = data.best_category;

    // Hide fields that are null or N/A
    hideIfNA('gmp');
    hideIfNA('price-high');
    hideIfNA('issue-size');
    hideIfNA('retail-sub');
    hideIfNA('hni-sub');
    hideIfNA('qib-sub');
    hideIfNA('listing-gain');
    hideIfNA('best-category');
}

function hideIfNA(id) {
    const element = document.getElementById(id);
    if (element.textContent === 'N/A') {
        element.parentElement.style.display = 'none';
    } else {
        element.parentElement.style.display = 'flex';
    }
}