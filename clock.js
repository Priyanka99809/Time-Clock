const hamburger= document.querySelector(".hamburger");
const navMenu= document.querySelector(".list");
hamburger.addEventListener("click",()=>{
    hamburger.classList.toggle("active");
    navMenu.classList.toggle("active");

})
document.querySelectorAll(".country").forEach(n=>n.addEventListener("click",()=> {
    hamburger.classList.remove("active");
    navMenu.classList.remove("active");

}))