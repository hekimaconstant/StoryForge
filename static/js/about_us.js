function openWhatsApp() {
    const name = document.getElementById('name').value;
    const email = document.getElementById('email').value;
    const message = document.getElementById('message').value;
    const discovery = document.getElementById('discovery').value;
    const phoneNumber = "{{ phone_number|safe }}";
    
    const textStr = `Name: ${name}\nEmail: ${email}\nDiscovery: ${discovery}\nMessage: ${message}`
    
    const encodedText = encodeURIComponent(textStr);
    
    window.open(`https://wa.me/${phoneNumber}?text=${encodedText}`, '_blank');
}