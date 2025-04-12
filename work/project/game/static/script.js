// script.js

document.addEventListener("DOMContentLoaded", function() {
    console.log("Custom script loaded.");

    // 카드 보드 페이지에서 클릭 시 간단한 애니메이션을 위해 (서버 이동 전) flip 클래스를 추가하는 예제입니다.
    // 만약 <a> 태그로 감싸져 있다면 실제 페이지 이동이 먼저 일어나므로,
    // 프론트엔드 애니메이션 효과를 적용하려면 별도 이벤트 처리가 필요합니다.
    let cards = document.querySelectorAll(".card");
    cards.forEach(card => {
        card.addEventListener("click", function(event) {
            // 이미 뒤집힌 경우 효과 적용 X
            if (!card.classList.contains("flipped")) {
                card.classList.add("flipped");
            }
        });
    });
});
