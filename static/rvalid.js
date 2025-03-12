function rValidate(){
    var names = document.getElementById('fname').value;
    var email = document.getElementById('femail').value;
    var phone = document.getElementById('fphone').value;
    var type = document.getElementById('ftype').value;
    var details = document.getElementById('fdetails').value;

    if(names.length < 3){
        alert("Enter your full name..!")
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
        alert("Your application has been submitted...!")
    }
}