<?php

namespace KanboardTests\units\Controller;

use Kanboard\Controller\DashboardController;
use Kanboard\Core\Http\Request;
use Kanboard\Core\Http\Response;
use Kanboard\Helper\LayoutHelper;
use Kanboard\Model\TaskModel;
use KanboardTests\units\Base;

class DashboardControllerTest extends Base
{
    public function testShowCountsAssignedTasksInReview()
    {
        $user = $this->container['userModel']->getById(1);
        $this->container['userSession']->initialize($user);

        $projectId = $this->container['projectModel']->create(array('name' => 'Dashboard project'), 1, true);
        $this->assertGreaterThan(0, $projectId);

        $reviewColumnId = $this->container['columnModel']->getColumnIdByTitle($projectId, 'In Review');
        $this->assertGreaterThan(0, $reviewColumnId);

        $taskId = $this->container['taskCreationModel']->create(array(
            'project_id' => $projectId,
            'column_id' => $reviewColumnId,
            'owner_id' => 1,
            'title' => 'Review the dashboard',
        ));
        $this->assertGreaterThan(0, $taskId);

        $data = $this->showDashboard($user);

        $this->assertEquals(1, $data['my_tasks_count']);
        $this->assertEquals(1, $data['in_review_count']);
        $this->assertEquals(0, $data['overdue_count']);
        $this->assertEquals(1, $data['projects_count']);
        $this->assertIsArray($data['recent_activity']);
    }

    public function testShowIsEmptyForUserWithoutProjects()
    {
        $userId = $this->container['userModel']->create(array('username' => 'dashboard-reader'));
        $this->assertGreaterThan(0, $userId);
        $user = $this->container['userModel']->getById($userId);

        $data = $this->showDashboard($user);

        $this->assertEquals(0, $data['my_tasks_count']);
        $this->assertEquals(0, $data['in_review_count']);
        $this->assertEquals(0, $data['overdue_count']);
        $this->assertEquals(0, $data['projects_count']);
        $this->assertSame(array(), $data['recent_activity']);
    }

    public function testShowRendersPersistedActivity()
    {
        $user = $this->container['userModel']->getById(1);
        $this->container['userSession']->initialize($user);
        $projectId = $this->container['projectModel']->create(array('name' => 'Activity project'), 1, true);
        $this->assertGreaterThan(0, $projectId);
        $taskId = $this->container['taskCreationModel']->create(array(
            'project_id' => $projectId,
            'owner_id' => 1,
            'title' => 'Dashboard activity event',
        ));
        $this->assertGreaterThan(0, $taskId);
        $this->container['projectActivityModel']->createEvent($projectId, $taskId, 1, TaskModel::EVENT_CREATE, array(
            'task' => $this->container['taskFinderModel']->getById($taskId),
        ));
        $this->assertNotEmpty($this->container['helper']->projectActivity->getProjectsEvents(array($projectId), 10));

        $this->configureRequest($user, true);
        $html = null;
        $response = $this->createMock(Response::class);
        $response->expects($this->once())
            ->method('html')
            ->willReturnCallback(function ($body) use (&$html) {
                $html = $body;
            });
        unset($this->container['response']);
        $this->container['response'] = $response;

        // Exercise the real overview template through the supported Ajax path.
        $controller = new DashboardController($this->container);
        $controller->show();

        $this->assertIsString($html);
        $this->assertStringContainsString('Recent Activity', $html);
        $this->assertStringContainsString('Dashboard activity event', $html);
    }

    private function configureRequest(array $user, $ajax = false)
    {
        $server = array(
            'REQUEST_METHOD' => 'GET',
            'SCRIPT_NAME' => '/index.php',
            'HTTP_HOST' => 'localhost',
            'SERVER_PORT' => 80,
        );
        if ($ajax) {
            $server['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest';
        }
        unset($this->container['request']);
        $this->container['request'] = new Request($this->container, $server, array('user_id' => $user['id']));
    }

    private function showDashboard(array $user)
    {
        $this->container['userSession']->initialize($user);
        $this->configureRequest($user);
        $data = null;

        $layout = $this->getMockBuilder(LayoutHelper::class)
            ->setConstructorArgs(array($this->container))
            ->onlyMethods(array('dashboard'))
            ->getMock();
        $layout->expects($this->once())
            ->method('dashboard')
            ->willReturnCallback(function ($template, $variables) use (&$data) {
                $this->assertSame('dashboard/overview', $template);
                $data = $variables;

                return 'dashboard-output';
            });
        $this->container['helper']->layout = $layout;

        $response = $this->createMock(Response::class);
        $response->expects($this->once())
            ->method('html')
            ->with('dashboard-output');
        unset($this->container['response']);
        $this->container['response'] = $response;

        $controller = new DashboardController($this->container);
        $controller->show();
        $this->assertIsArray($data);

        return $data;
    }
}
