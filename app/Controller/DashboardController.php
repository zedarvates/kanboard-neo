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

        // Compute real dashboard stats
        $projectIds = $this->projectPermissionModel->getActiveProjectIds($user['id']);
        $inReviewColumnIds = $this->getInReviewColumnIds($projectIds);
        $myTasks = $this->taskFinderModel->getUserQuery($user['id'])->count();
        $inReview = 0;

        if (! empty($inReviewColumnIds)) {
            $inReview = $this->db->table(TaskModel::TABLE)
                ->eq('owner_id', $user['id'])
                ->eq('is_active', TaskModel::STATUS_OPEN)
                ->in('column_id', $inReviewColumnIds)
                ->count();
        }
        $overdue = $this->taskFinderModel->getOverdueTasksByUser($user['id']);
        $projectsCount = $projectIds;
        $recentActivity = empty($projectIds)
            ? array()
            : $this->helper->projectActivity->getProjectsEvents($projectIds, 10);

        $this->response->html($this->helper->layout->dashboard('dashboard/overview', array(
            'title'              => t('Dashboard for %s', $this->helper->user->getFullname($user)),
            'user'               => $user,
            'overview_paginator' => $this->dashboardPagination->getOverview($user['id']),
            'project_paginator'  => $this->projectPagination->getDashboardPaginator($user['id'], 'show', DASHBOARD_MAX_PROJECTS),
            'my_tasks_count'     => $myTasks,
            'in_review_count'    => $inReview,
            'overdue_count'      => is_array($overdue) ? count($overdue) : $overdue,
            'projects_count'     => is_array($projectsCount) ? count($projectsCount) : $projectsCount,
            'recent_activity'    => $recentActivity,
        )));
    }

    /**
     * Get column IDs that represent "in review" status
     */
    private function getInReviewColumnIds(array $projectIds): array
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
