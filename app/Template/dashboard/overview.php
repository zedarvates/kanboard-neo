<?= $this->hook->render('template:dashboard:show:before-filter-box', array('user' => $user)) ?>

<div class="dashboard-stats">
    <div class="dashboard-stat-card">
        <div class="stat-value"><?= $project_paginator->getTotal() ?></div>
        <div class="stat-label">Projects</div>
    </div>
    <div class="dashboard-stat-card">
        <div class="stat-value">0</div>
        <div class="stat-label">My Tasks</div>
    </div>
    <div class="dashboard-stat-card">
        <div class="stat-value">0</div>
        <div class="stat-label">In Review</div>
    </div>
    <div class="dashboard-stat-card">
        <div class="stat-value">0</div>
        <div class="stat-label">Overdue</div>
    </div>
</div>

<div class="filter-box margin-bottom">
    <form method="get" action="<?= $this->url->dir() ?>" class="search">
        <?= $this->form->hidden('controller', array('controller' => 'SearchController')) ?>
        <?= $this->form->hidden('action', array('action' => 'index')) ?>

        <div class="input-addon">
            <?= $this->form->text('search', array(), array(), array('placeholder="Search tasks, projects..."', 'aria-label="'.t('Search').'"'), 'input-addon-field') ?>
            <div class="input-addon-item">
                <?= $this->render('app/filters_helper') ?>
            </div>
        </div>
    </form>
</div>

<?= $this->hook->render('template:dashboard:show:after-filter-box', array('user' => $user)) ?>

<?php if (! $project_paginator->isEmpty()): ?>
    <div class="section-title">
        <h2>Projects</h2>
        <span class="section-count"><?= $project_paginator->getTotal() ?></span>
    </div>
    <div class="table-list">
        <?= $this->render('project_list/header', array('paginator' => $project_paginator)) ?>
        <?php foreach ($project_paginator->getCollection() as $project): ?>
            <div class="table-list-row table-border-left">
                <div>
                    <?php if ($this->user->hasProjectAccess('ProjectViewController', 'show', $project['id'])): ?>
                        <?= $this->render('project/dropdown', array('project' => $project)) ?>
                    <?php else: ?>
                        <strong><?= '#'.$project['id'] ?></strong>
                    <?php endif ?>

                    <?= $this->hook->render('template:dashboard:project:before-title', array('project' => $project)) ?>

                    <span class="table-list-title <?= $project['is_active'] == 0 ? 'status-closed' : '' ?>">
                        <?= $this->url->link($this->text->e($project['name']), 'BoardViewController', 'show', array('project_id' => $project['id'])) ?>
                    </span>

                    <?php if ($project['is_private']): ?>
                        <i class="fa fa-lock fa-fw" title="<?= t('Personal project') ?>" role="img" aria-label="<?= t('Personal project') ?>"></i>
                    <?php endif ?>

                    <?= $this->hook->render('template:dashboard:project:after-title', array('project' => $project)) ?>

                </div>
                <div class="table-list-details">
                    <?php foreach ($project['columns'] as $column): ?>
                        <span class="column-badge">
                            <strong><?= $column['nb_open_tasks'] ?></strong>
                            <small><?= $this->text->e($column['title']) ?></small>
                        </span>
                    <?php endforeach ?>
                </div>
            </div>
        <?php endforeach ?>
    </div>

    <?= $project_paginator ?>
<?php endif ?>

<?php if (empty($overview_paginator)): ?>
    <div class="empty-state">
        <div class="empty-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#2E2E2E" stroke-width="1.5">
                <path d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/>
                <path d="M9 14l2 2 4-4"/>
            </svg>
        </div>
        <p class="empty-text">Nothing assigned to you</p>
        <p class="empty-hint">Tasks assigned to you will appear here</p>
    </div>
<?php else: ?>
    <?php foreach ($overview_paginator as $result): ?>
        <?php if (! $result['paginator']->isEmpty()): ?>
            <div class="section-title">
                <h2 id="project-tasks-<?= $result['project_id'] ?>">
                    <?= $this->url->link($this->text->e($result['project_name']), 'BoardViewController', 'show', array('project_id' => $result['project_id'])) ?>
                </h2>
                <span class="section-count"><?= $result['paginator']->getTotal() ?></span>
            </div>

            <div class="table-list">
                <?= $this->render('task_list/header', array(
                    'paginator' => $result['paginator'],
                )) ?>

                <?php foreach ($result['paginator']->getCollection() as $task): ?>
                    <div class="table-list-row color-<?= $task['color_id'] ?>">
                        <?= $this->render('task_list/task_title', array(
                            'task' => $task,
                            'redirect' => 'dashboard',
                        )) ?>

                        <?= $this->render('task_list/task_details', array(
                            'task' => $task,
                        )) ?>

                        <?= $this->render('task_list/task_avatars', array(
                            'task' => $task,
                        )) ?>

                        <?= $this->render('task_list/task_icons', array(
                            'task' => $task,
                        )) ?>

                        <?= $this->render('task_list/task_subtasks', array(
                            'task'    => $task,
                            'user_id' => $user['id'],
                        )) ?>

                        <?= $this->hook->render('template:dashboard:task:footer', array('task' => $task)) ?>
                    </div>
                <?php endforeach ?>
            </div>

            <?= $result['paginator'] ?>
        <?php endif ?>
    <?php endforeach ?>
<?php endif ?>

<?= $this->hook->render('template:dashboard:show', array('user' => $user)) ?>
