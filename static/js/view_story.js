document.querySelectorAll('.view-user-link').forEach(link => {
    link.addEventListener('click', function(event) {
        if (this.getAttribute('target') === '_blank') {
            return;
    }

    event.preventDefault();

    const linkContent = this.innerText.toLowerCase();

    fetch('/view-user', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text_content: linkContent })
        })
        .then(response => response.json())
        .then(data => {
            console.log('Flask received it:', data);

            // Load the page after response in the SAME tab
            window.location.href = this.getAttribute('href');
        });
    });
});