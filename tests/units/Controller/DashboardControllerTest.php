<?php

namespace KanboardTests\units\Controller;

use Kanboard\Controller\DashboardController;
use KanboardTests\units\Base;

class TestableDashboardController extends DashboardController
{
    public function dashboardData(array $user)
    {
        return $this->getDashboardData($user);
    }
}

class DashboardControllerTest extends Base
{
    public function testDashboardDataUsesExistingQueriesAndCountsReviewTasks()
    {
        $user = $this->container['userModel']->getById(1);
        $this->container['userSession']->initialize($user);

        $projectId = $this->container['projectModel']->create(array('name' => 'Portfolio Cockpit'), 1, true);
        $this->assertEquals(1, $projectId);

        $reviewColumnId = $this->container['columnModel']->getColumnIdByTitle($projectId, 'In Review');
        $this->assertGreaterThan(0, $reviewColumnId);

        $taskId = $this->container['taskCreationModel']->create(array(
            'project_id' => $projectId,
            'column_id' => $reviewColumnId,
            'owner_id' => 1,
            'title' => 'Review the portfolio registry',
        ));
        $this->assertEquals(1, $taskId);

        $controller = new TestableDashboardController($this->container);
        $data = $controller->dashboardData($user);

        $this->assertEquals(1, $data['my_tasks_count']);
        $this->assertEquals(1, $data['in_review_count']);
        $this->assertEquals(0, $data['overdue_count']);
        $this->assertEquals(1, $data['projects_count']);
        $this->assertIsArray($data['recent_activity']);
    }

    public function testDashboardDataIsEmptyForUserWithoutProjects()
    {
        $userId = $this->container['userModel']->create(array('username' => 'portfolio-reader'));
        $this->assertEquals(2, $userId);

        $user = $this->container['userModel']->getById($userId);
        $this->container['userSession']->initialize($user);

        $controller = new TestableDashboardController($this->container);
        $data = $controller->dashboardData($user);

        $this->assertEquals(0, $data['my_tasks_count']);
        $this->assertEquals(0, $data['in_review_count']);
        $this->assertEquals(0, $data['overdue_count']);
        $this->assertEquals(0, $data['projects_count']);
        $this->assertSame(array(), $data['recent_activity']);
    }
}
