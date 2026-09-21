document.querySelectorAll('.video-quality').forEach(select => {
  select.addEventListener('change', () => {
    const video = select.closest('article').querySelector('video');
    const option = select.selectedOptions[0];
    video.pause();
    video.src = option.value;
    if (option.dataset.poster) video.poster = option.dataset.poster;
    else video.removeAttribute('poster');
    video.preload = 'metadata';
    video.load();
  });
});
