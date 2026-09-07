<?php

namespace KanboardTests\integration;

class ColumnProcedureTest extends BaseProcedureTest
{
    protected $projectName = 'My project to test columns';
    private $columns = array();

    public function testAll()
    {
        $this->assertCreateTeamProject();
        $this->assertGetColumns();
        $this->assertUpdateColumn();
        $this->assertAddColumn();
        $this->assertRemoveColumn();
        $this->assertChangeColumnPosition();
    }

    public function assertGetColumns()
    {
        $this->columns = $this->app->getColumns($this->projectId);
        $this->assertCount(6, $this->columns);
        $this->assertEquals(
            array('Triage', 'Backlog', 'Started', 'In Review', 'Done', 'Canceled'),
            array_column($this->columns, 'title')
        );
    }

    public function assertUpdateColumn()
    {
        $this->assertTrue($this->app->updateColumn($this->columns[3]['id'], 'Another column', 2));

        $this->columns = $this->app->getColumns($this->projectId);
        $this->assertEquals('Another column', $this->columns[3]['title']);
        $this->assertEquals(2, $this->columns[3]['task_limit']);
    }

    public function assertAddColumn()
    {
        $column_id = $this->app->addColumn($this->projectId, 'New column');
        $this->assertNotFalse($column_id);
        $this->assertTrue($column_id > 0);

        $this->columns = $this->app->getColumns($this->projectId);
        $this->assertCount(7, $this->columns);
        $this->assertEquals('New column', $this->columns[6]['title']);
    }

    public function assertRemoveColumn()
    {
        $this->assertTrue($this->app->removeColumn($this->columns[3]['id']));

        $this->columns = $this->app->getColumns($this->projectId);
        $this->assertCount(6, $this->columns);
    }

    public function assertChangeColumnPosition()
    {
        $this->assertTrue($this->app->changeColumnPosition($this->projectId, $this->columns[0]['id'], 3));

        $this->columns = $this->app->getColumns($this->projectId);
        $this->assertEquals(
            array('Backlog', 'Started', 'Triage', 'Done', 'Canceled', 'New column'),
            array_column($this->columns, 'title')
        );
        $this->assertEquals(
            array(1, 2, 3, 4, 5, 6),
            array_column($this->columns, 'position')
        );
    }

    public function testChangeColumnPositionCannotModifyColumnFromAnotherProjectWithForgedProjectId()
    {
        $projectIdA = $this->manager->createProject(array(
            'name' => 'Project A',
            'owner_id' => $this->managerUserId,
        ));

        $projectIdB = $this->manager->createProject(array(
            'name' => 'Project B',
            'owner_id' => $this->managerUserId,
        ));

        $this->assertNotFalse($projectIdA);
        $this->assertNotFalse($projectIdB);
        $this->assertTrue($this->manager->addProjectUser($projectIdA, $this->userUserId, 'project-manager'));

        $columnIdB = $this->manager->addColumn($projectIdB, 'Project B column');
        $this->assertNotFalse($columnIdB);

        $this->assertFalse($this->user->changeColumnPosition($projectIdA, $columnIdB, 1));

        $columnB = $this->manager->getColumn($columnIdB);
        $this->assertEquals($projectIdB, $columnB['project_id']);
    }
}
