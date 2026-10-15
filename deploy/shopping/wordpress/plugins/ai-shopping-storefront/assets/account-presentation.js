document.addEventListener("click", event => {
  const logout = event.target.closest("[data-aicc-prod-logout]");
  if (!logout) return;
  if (!window.confirm("로그아웃하시겠습니까?")) event.preventDefault();
});
