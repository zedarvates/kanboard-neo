<div class="form-login">

    <?= $this->hook->render('template:auth:login-form:before') ?>

    <div class="login-logo">
        <svg width="40" height="40" viewBox="0 0 40 40" fill="none">
            <rect width="40" height="40" rx="10" fill="#5E6AD2"/>
            <path d="M12 28V12h6.5a6 6 0 010 12H18v4h-6zm6-8a2 2 0 000-4h-2v4h2z" fill="white"/>
            <path d="M22 28V12h6a4 4 0 013.5 6 4 4 0 01-3.5 6h-2v4h-4zm4-8a2 2 0 000-4h-2v4h2z" fill="white" opacity="0.8"/>
        </svg>
        <h1>Kanboard Neo</h1>
        <p class="login-subtitle">Project management, reimagined</p>
    </div>

    <?php if (isset($errors['login'])): ?>
        <p class="alert alert-error"><?= $this->text->e($errors['login']) ?></p>
    <?php endif ?>

    <?php if (! HIDE_LOGIN_FORM): ?>
    <form method="post" action="<?= $this->url->href('AuthController', 'check') ?>">

        <?= $this->form->csrf() ?>

        <div class="login-field">
            <?= $this->form->label(t('Username'), 'username') ?>
            <?= $this->form->text('username', $values, $errors, array('autofocus', 'required', 'autocomplete="username"', 'placeholder="Enter your username"')) ?>
        </div>

        <div class="login-field">
            <?= $this->form->label(t('Password'), 'password') ?>
            <?= $this->form->password('password', $values, $errors, array('required', 'autocomplete="current-password"', 'placeholder="Enter your password"')) ?>
        </div>

        <?php if (isset($captcha) && $captcha): ?>
            <?= $this->form->label(t('Enter the text below'), 'captcha') ?>
            <img src="<?= $this->url->href('CaptchaController', 'image') ?>" alt="Captcha">
            <?= $this->form->text('captcha', array(), $errors, array('required')) ?>
        <?php endif ?>

        <?php if (REMEMBER_ME_AUTH): ?>
            <label class="login-checkbox">
                <?= $this->form->checkbox('remember_me', t('Remember Me'), 1, true) ?>
            </label><br>
        <?php endif ?>

        <div class="form-actions">
            <button type="submit" class="btn btn-blue login-btn"><?= t('Sign in') ?></button>
        </div>
        <?php if ($this->app->config('password_reset') == 1): ?>
            <div class="reset-password">
                <?= $this->url->link(t('Forgot password?'), 'PasswordResetController', 'create') ?>
            </div>
        <?php endif ?>
    </form>
    <?php endif ?>

    <?= $this->hook->render('template:auth:login-form:after') ?>
</div>
