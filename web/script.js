const langData = {
    vi: {
        title: "GIF Overlay - Ứng dụng hiển thị ảnh GIF nổi trên màn hình",
        subtitle: "Dễ dàng tùy chỉnh kích thước, vị trí, độ mờ và nhiều tính năng tiện ích khác.",
        downloadText: "Tải Ngay",
        sourceCode: "Mã Nguồn",
        feature1Title: "Hiển thị GIF nổi",
        feature1Desc: "Hiển thị GIF không viền, trong suốt và luôn nổi trên cùng mọi cửa sổ khác.",
        feature2Title: "Tùy chỉnh dễ dàng",
        feature2Desc: "Thay đổi kích thước, độ mờ và vị trí lưu tự động, khóa cửa sổ tiện lợi.",
        feature3Title: "Tiết kiệm CPU",
        feature3Desc: "Tạm dừng hoặc phát GIF theo ý muốn để giảm tải cho hệ thống.",
        feature4Title: "Lưu và sử dụng lại",
        feature4Desc: "Lưu ảnh GIF và mở lại dễ dàng, thu nhỏ vào khay hệ thống tiện dụng.",
        publishDate: "Đăng ngày: 7 tháng 6 năm 2025",
        aboutTitle: "Giới thiệu về GIF Overlay",
        aboutP1: "<strong>GIF Overlay</strong> là ứng dụng giúp bạn hiển thị ảnh GIF nổi trên màn hình Windows, với nhiều tính năng tiện lợi giúp cá nhân hóa trải nghiệm làm việc và giải trí.",
        aboutP2: "Ứng dụng được phát triển nhằm mục đích đơn giản, nhẹ nhàng, dễ sử dụng và có khả năng tùy chỉnh đa dạng: thay đổi kích thước, độ mờ, vị trí lưu, khóa cửa sổ không cho di chuyển, tạm dừng hoặc phát GIF theo ý muốn, cũng như lưu ảnh GIF và sử dụng lại dễ dàng.",
        aboutP3: "Với GIF Overlay, bạn có thể làm cho màn hình trở nên sinh động và cá tính hơn mà không ảnh hưởng đến hiệu năng hệ thống."
    },
    en: {
        title: "GIF Overlay - Floating GIF Display Application",
        subtitle: "Easily customize size, position, opacity, and many other useful features.",
        downloadText: "Download Now",
        sourceCode: "Source Code",
        feature1Title: "Floating GIF Display",
        feature1Desc: "Display borderless, transparent GIFs that always stay on top of other windows.",
        feature2Title: "Easy Customization",
        feature2Desc: "Change size, opacity, save position automatically, and lock the window easily.",
        feature3Title: "CPU Saving",
        feature3Desc: "Pause or play GIFs as you want to reduce system load.",
        feature4Title: "Save & Reuse",
        feature4Desc: "Save GIF images and easily reopen, minimize to system tray.",
        publishDate: "Published: June 7, 2025",
        aboutTitle: "About GIF Overlay",
        aboutP1: "<strong>GIF Overlay</strong> is an application that helps you display floating GIFs on Windows screen, with many useful features to personalize your work and entertainment experience.",
        aboutP2: "The app is developed to be simple, lightweight, easy to use, and supports versatile customization: resize, opacity, save position, lock window, pause/play GIF, and easy reuse.",
        aboutP3: "With GIF Overlay, you can make your screen more lively and personal without affecting system performance."
    }
};

function changeLanguage(lang) {
    const data = langData[lang];
    document.documentElement.lang = lang;
    document.getElementById("title").textContent = data.title;
    document.getElementById("subtitle").textContent = data.subtitle;
    document.getElementById("download-text").textContent = data.downloadText;
    document.getElementById("source-code-link").textContent = data.sourceCode;
    document.getElementById("feature1-title").textContent = data.feature1Title;
    document.getElementById("feature1-desc").textContent = data.feature1Desc;
    document.getElementById("feature2-title").textContent = data.feature2Title;
    document.getElementById("feature2-desc").textContent = data.feature2Desc;
    document.getElementById("feature3-title").textContent = data.feature3Title;
    document.getElementById("feature3-desc").textContent = data.feature3Desc;
    document.getElementById("feature4-title").textContent = data.feature4Title;
    document.getElementById("feature4-desc").textContent = data.feature4Desc;
    document.getElementById("publish-date").textContent = data.publishDate;
    document.getElementById("about-title").textContent = data.aboutTitle;
    document.getElementById("about-p1").innerHTML = data.aboutP1;
    document.getElementById("about-p2").textContent = data.aboutP2;
    document.getElementById("about-p3").textContent = data.aboutP3;
}

// Set default language to English
document.addEventListener('DOMContentLoaded', () => {
    changeLanguage('en');
    document.getElementById('lang-select').value = 'en';
});
