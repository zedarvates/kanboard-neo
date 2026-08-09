<?php

namespace KanboardTests\integration;

class BoardProcedureTest extends BaseProcedureTest
{
    protected $projectName = 'My project to test board';

    public function testAll()
    {
        $this->assertCreateTeamProject();
        $this->assertGetBoard();
    }

    public function assertGetBoard()
    {
        $board = $this->app->getBoard($this->projectId);
        $this->assertNotNull($board);
        $this->assertCount(1, $board);
        $this->assertEquals('Default swimlane', $board[0]['name']);

        $this->assertCount(6, $board[0]['columns']);
        $this->assertSame(
            array('Triage', 'Backlog', 'Started', 'In Review', 'Done', 'Canceled'),
            array_column($board[0]['columns'], 'title')
        );
    }
}
