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
        $this->assertEquals('Triage', $board[0]['columns'][0]['title']);
        $this->assertEquals('Backlog', $board[0]['columns'][1]['title']);
        $this->assertEquals('Started', $board[0]['columns'][2]['title']);
        $this->assertEquals('In Review', $board[0]['columns'][3]['title']);
        $this->assertEquals('Done', $board[0]['columns'][4]['title']);
        $this->assertEquals('Canceled', $board[0]['columns'][5]['title']);
    }
}
