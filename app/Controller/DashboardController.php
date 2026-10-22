<?php

namespace Kanboard\Controller;

use Kanboard\Model\ColumnModel;
use Kanboard\Model\TaskModel;

/**
 * Dashboard Controller
 *
 * @package  Kanboard\Controller
 * @author   Frederic Guillot
 */
class DashboardController extends BaseController
{
    /**
     * Dashboard overview
     *
     * @access public
     */
    public function show()
    {
        $user = $this->getUser();
        $dashboardData = $this->getDashboardData($user);

        $this->response->html($this->helper->layout->dashboard('dashboard/overview', array_merge(array(
            'title'              => t('Dashboard for %s', $this->helper->user->getFullname($user)),
            'user'               => $user,
            'overview_paginator' => $this->dashboardPagination->getOverview($user['id']),
            'project_paginator'  => $this->projectPagination->getDashboardPaginator($user['id'], 'show', DASHBOARD_MAX_PROJECTS),
        ), $dashboardData)));
    }

    /**
     * Build the dynamic dashboard counters and activity feed.
     *
     * @param array $user
     * @return array
     */
    protected function getDashboardData(array $user)
    {
        $projectIds = $this->projectPermissionModel->getActiveProjectIds($user['id']);
        $inReviewColumnIds = $this->getInReviewColumnIds($projectIds);
        $inReviewCount = 0;

        if (! empty($inReviewColumnIds)) {
            $inReviewCount = $this->db->table(TaskModel::TABLE)
                ->eq(TaskModel::TABLE.'.owner_id', $user['id'])
                ->eq(TaskModel::TABLE.'.is_active', TaskModel::STATUS_OPEN)
                ->in(TaskModel::TABLE.'.column_id', $inReviewColumnIds)
                ->count();
        }

        return array(
            'my_tasks_count' => $this->taskFinderModel->getUserQuery($user['id'])->count(),
            'in_review_count' => $inReviewCount,
            'overdue_count' => count($this->taskFinderModel->getOverdueTasksByUser($user['id'])),
            'projects_count' => count($projectIds),
            'recent_activity' => empty($projectIds)
                ? array()
                : $this->helper->projectActivity->getProjectsEvents($projectIds, 10),
        );
    }

    /**
     * Get column IDs that represent "in review" status.
     *
     * @param array $projectIds
     * @return array
     */
    protected function getInReviewColumnIds(array $projectIds)
    {
        if (empty($projectIds)) {
            return array();
        }

        return $this->db->table(ColumnModel::TABLE)
            ->eq(ColumnModel::TABLE.'.hide_in_dashboard', 0)
            ->in(ColumnModel::TABLE.'.project_id', $projectIds)
            ->ilike(ColumnModel::TABLE.'.title', '%review%')
            ->findAllByColumn(ColumnModel::TABLE.'.id');
    }

    /**
     * My tasks
     *
     * @access public
     */
    public function tasks()
    {
        $user = $this->getUser();

        $this->response->html($this->helper->layout->dashboard('dashboard/tasks', array(
            'title' => t('Tasks overview for %s', $this->helper->user->getFullname($user)),
            'paginator' => $this->taskPagination->getDashboardPaginator($user['id'], 'tasks', 50),
            'user' => $user,
        )));
    }

    /**
     * My subtasks
     *
     * @access public
     */
    public function subtasks()
    {
        $user = $this->getUser();

        $this->response->html($this->helper->layout->dashboard('dashboard/subtasks', array(
            'title' => t('Subtasks overview for %s', $this->helper->user->getFullname($user)),
            'paginator' => $this->subtaskPagination->getDashboardPaginator($user['id']),
            'user' => $user,
            'nb_subtasks' => $this->subtaskModel->countByAssigneeAndTaskStatus($user['id']),
        )));
    }

    /**
     * My projects
     *
     * @access public
     */
    public function projects()
    {
        $user = $this->getUser();

        $this->response->html($this->helper->layout->dashboard('dashboard/projects', array(
            'title' => t('Projects overview for %s', $this->helper->user->getFullname($user)),
            'paginator' => $this->projectPagination->getDashboardPaginator($user['id'], 'projects', 25),
            'user' => $user,
        )));
    }
}
