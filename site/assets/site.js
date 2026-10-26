/* DreamsCatalyst site.js: replaces the GoDaddy runtime, whose scripts no longer load.
   Handles the hamburger navigation drawer, the FAQ accordion and the contact form. */
(function () {
  'use strict';

  // ---------- 1. Navigation drawer (hamburger) ----------
  var openDrawer = null;
  var opener = null;

  function setDrawer(drawer, btn, open) {
    if (!drawer) return;
    drawer.style.transform = open ? 'translateX(0)' : '';
    drawer.style.visibility = open ? 'visible' : '';
    document.documentElement.style.overflow = open ? 'hidden' : '';
    if (btn) btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    openDrawer = open ? drawer : null;
    opener = open ? btn : null;
    if (open) {
      var first = drawer.querySelector('a[href]');
      if (first) first.focus();
    } else if (btn) {
      btn.focus();
    }
  }

  document.addEventListener('click', function (e) {
    var btn = e.target.closest('[data-aid="HAMBURGER_MENU_LINK"][toggleid]');
    if (btn) {
      e.preventDefault();
      var drawer = document.getElementById(btn.getAttribute('toggleid'));
      setDrawer(drawer, btn, drawer !== openDrawer);
      return;
    }
    if (openDrawer) {
      if (e.target.closest('[data-close]')) {
        e.preventDefault();
        setDrawer(openDrawer, opener, false);
        return;
      }
      if (!openDrawer.contains(e.target)) setDrawer(openDrawer, opener, false);
    }

    // ---------- 2. FAQ accordion: the page CSS already shows an answer when aria-expanded="true" ----------
    var q = e.target.closest('.accordion-question');
    if (q) {
      e.preventDefault();
      q.setAttribute('aria-expanded', q.getAttribute('aria-expanded') === 'true' ? 'false' : 'true');
    }
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && openDrawer) setDrawer(openDrawer, opener, false);
  });

  // ---------- 3. Contact form ----------
  var MSG = {
    en: {
      sending: 'Sending…',
      ok: 'Thank you! Your message has been sent. Mika will get back to you soon.',
      err: 'Sorry, your message could not be sent. Please email mika@dreamscatalyst.com or text (408) 475-6452.',
      email: 'Please enter a valid email address.'
    },
    ko: {
      sending: '전송 중…',
      ok: '감사합니다! 메시지가 전송되었습니다. Mika가 곧 연락드리겠습니다.',
      err: '죄송합니다. 메시지를 보내지 못했습니다. mika@dreamscatalyst.com으로 이메일을 보내시거나 (408) 475-6452로 문자해 주세요.',
      email: '올바른 이메일 주소를 입력해 주세요.'
    },
    ja: {
      sending: '送信中…',
      ok: 'ありがとうございます！メッセージを送信しました。Mikaより折り返しご連絡いたします。',
      err: '申し訳ありません。メッセージを送信できませんでした。mika@dreamscatalyst.com までメール、または (408) 475-6452 までテキストメッセージをお送りください。',
      email: '有効なメールアドレスを入力してください。'
    },
    'zh-Hans': {
      sending: '正在发送…',
      ok: '谢谢！您的留言已发送，Mika 会尽快与您联系。',
      err: '抱歉，留言发送失败。请发送邮件至 mika@dreamscatalyst.com，或发短信至 (408) 475-6452。',
      email: '请输入有效的电子邮件地址。'
    }
  };
  var T = MSG[document.documentElement.lang] || MSG.en;
  var NL = String.fromCharCode(10);

  function showStatus(form, text, isError) {
    var el = form.querySelector('.dc-form-status');
    if (!el) {
      el = document.createElement('p');
      el.className = 'dc-form-status';
      el.setAttribute('role', 'status');
      el.style.cssText = 'margin:12px 0 0;font-size:15px;line-height:1.4;';
      form.appendChild(el);
    }
    el.style.color = isError ? '#b00020' : '#0a636e';
    el.textContent = text;
  }

  document.querySelectorAll('form[data-dc-contact]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var fd = new FormData(form);
      if (fd.get('_gotcha')) return; // honeypot filled in: a bot
      var emailField = form.querySelector('[name="email"]');
      var email = String(fd.get('email') || '').trim();
      if (!email || (emailField && !emailField.checkValidity())) {
        showStatus(form, T.email, true);
        return;
      }
      var endpoint = form.getAttribute('data-endpoint');
      if (!endpoint) {
        // No form service configured yet: hand the message to the visitor's email app.
        var body = 'Name: ' + (fd.get('name') || '') + NL + 'Email: ' + email + NL + NL + (fd.get('message') || '');
        window.location.href = 'mailto:mika@dreamscatalyst.com?subject=' +
          encodeURIComponent('Website inquiry') + '&body=' + encodeURIComponent(body);
        return;
      }
      showStatus(form, T.sending, false);
      fetch(endpoint, { method: 'POST', body: fd, headers: { Accept: 'application/json' } })
        .then(function (r) {
          if (!r.ok) throw new Error('HTTP ' + r.status);
          form.reset();
          showStatus(form, T.ok, false);
        })
        .catch(function () {
          showStatus(form, T.err, true);
        });
    });
  });
})();
