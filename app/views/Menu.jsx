'use babel';

import React from 'react';

export default class Menu extends React.Component {

    render() {
        return <div className="menu">
            <Button label="Save" action={this.props.io.save}/>
            <Button label="Load" action={this.props.io.load}/>
            <Button label="Export" action={this.props.io.exp}/>
        </div>;
    }
}


class Button extends React.Component {
    render() {
        return <div onClick={this.props.action}>{this.props.label}</div>
    }
}
