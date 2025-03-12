function dValidate(){
    var names = document.getElementById('fname').value;
    var age = document.getElementById('fage').value;
    var weight = document.getElementById('fweight').value;
    var email = document.getElementById('femail').value;
    var phone = document.getElementById('fphone').value;
    var type = document.getElementById('ftype').value;
    var details = document.getElementById('fdetails').value;

    if(names.length < 3){
        alert("Enter your full name..!")
        return false
    } else if (age.length < 1) {
        alert("Enter valid age..!")
        return false
    } else if (weight.length < 2) {
        alert("Enter valid weight...!")
        return false
    } else if (email.length < 3) {
        alert("Enter your email address..!")
        return false
    } else if (phone.length < 10) {
        alert("Enter a valid phone number..!")
        return false
    } else if (type.length < 2) {
        alert("Enter you blood type..!")
        return false
    } else if (details.length < 15) {
        alert("Fill your details")
        return false
    } else {
        alert("Your appointment has been booked...! You will recieve a phone call for all instructions.")
    }
}