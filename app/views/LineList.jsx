'use babel';

import React from 'react';
import update from 'react/lib/update';
import { DragSource, DropTarget } from 'react-dnd';

import Line from './Line';

var Waypoint = require('react-waypoint');

const knex = require('../db').knex;

export class Play extends React.Component{
    handleClick = (e) => {
        this.props.playAll();
    }

    render(){
        return <div className="button" onClick={this.handleClick}>Play all</div>
    }
}

export class Container extends React.Component{
    constructor(props){
        super(props);
        this.state = {lines: []};
    }

    renderLines(moreProps) {
        let lineNodes = this.state.lines.map( (line, i) => {
            let id = line.movie_id.toString() + line.start.toString();
            return <Line data={line}
                  index={i}
                  id={id}
                  ref={id}
                  key={id}
                  {...moreProps}
            />
        });
        return lineNodes;

    }

    render() {
        return <ul className="container">
            {this.renderLines()}
        </ul>;
    };

}


const containerTarget = {
  drop(props, monitor, component) {
    const hasDroppedOnChild = monitor.didDrop();
    if (hasDroppedOnChild) {
        return;
    }
    const dragIndex = monitor.getItem().index;
    monitor.getItem().removeLine(dragIndex);
    component.addLine(-1, monitor.getItem().data);
  }
}

@DropTarget('line', containerTarget, (connect, monitor) => ({
  connectDropTarget: connect.dropTarget(),
  isOver: monitor.isOver({shallow: true})
}))
export class SortableContainer extends Container {
    constructor(props){
        super(props);
        this.removeLine = this.removeLine.bind(this);
        this.addLine = this.addLine.bind(this);
        this.playAll = this.playAll.bind(this);
    }

    removeLine(dragIndex) {
        this.setState(update(this.state, {
            lines: {
                $splice: [
                    [dragIndex, 1],
                ]
            }
        }));
    }

    addLine(hoverIndex, dragLine) {
        if (hoverIndex == -1){
            this.setState(update(this.state, {
                lines: {
                    $push: [ dragLine ]
                }
            }));
        } else {
            this.setState(update(this.state, {
                lines: {
                    $splice: [
                        [hoverIndex, 0, dragLine]
                    ]
                }
            }));
        }
    }

    playAll(){
        for (var r in this.refs){
            let line = this.refs[r].decoratedComponentInstance.decoratedComponentInstance;
            line.handleClick();
        }
    }

    render() {
        const { isOver, connectDropTarget } = this.props;
        let over = isOver ? 'over' : '';
        return connectDropTarget(
            <ul className={`container ${over}`}>
                {this.renderLines({removeLine: this.removeLine,
                                   addLine: this.addLine,
                                   draggable: true})}
            </ul>
        );
    };

}


export class DbContainer extends Container{
    componentDidMount(){
        // Trigger for initial render
        this.componentWillReceiveProps(this.props);
    }

    removeLine(dragIndex) {
        console.log('dragged from db');
    }

    addLine(hoverIndex, dragLine) {
    }

    componentWillReceiveProps(props){
        let query = knex.from('line')
                        .join('movie', 'movie.id', '=', 'line.movie_id')
                        .select('movie.title',
                                'movie.id',
                                'movie.framerate',
                                'movie.width',
                                'movie.height',
                                'movie.video',
                                'movie.total_duration',
                                'line.movie_id',
                                'line.start',
                                'line.duration',
                                'line.text',
                                'line.audio',
                                'line.sextimate')
                        .offset(0)
                        .limit(20);

        if (props.filter == ''){
            query.orderByRaw('RANDOM()')
        } else {
            query.where('text', 'like', '%'+props.filter+'%')
        }

        this.query = query;

        query.then( rows => {
            this.setState({'lines': rows});
        });
    }

    bottomReached() {
        // Fetch more results
        if (typeof this.query != 'undefined'){
            let so_far = this.query._single.offset + this.query._single.limit;

            this.query.offset(so_far).limit(30)
            .then ( rows => {
                this.setState({'lines': this.state.lines.concat(rows)});
            })
        }
    }

    render() {
        return <ul id="linelist" className="container">
            {super.renderLines({removeLine: this.removeLine,
                                addLine: this.addLine,
                                draggable: false})}
            <Waypoint ref="bottom" onEnter={() => this.bottomReached()} />
        </ul>;
    };
}
