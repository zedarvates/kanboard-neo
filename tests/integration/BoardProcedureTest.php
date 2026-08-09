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

        $expectedTitles = array('Triage', 'Backlog', 'Started', 'In Review', 'Done', 'Canceled');
        foreach ($expectedTitles as $index => $title) {
            $this->assertEquals($title, $board[0]['columns'][$index]['title']);
        }
    }
}
